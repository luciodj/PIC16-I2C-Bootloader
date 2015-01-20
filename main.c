/*
 * I2C High BootLoader for PIC16F1783 Buck Click
 *
 * File:   main.c
 * Author: Lucio Di Jasio
 *
 * Compiler: XC8, v.1.33b
 *
 * Created on January 16, 2015
 */
#include "mcc_generated_files/mcc.h"
#include "Flash.h"

#include <string.h>

// program memory organization for PIC16F1783
#define BOOT_START    0x0E00       // row aligned high start of bootloader
#define APP_START     BOOT_START-2 // ljmp to application 

inline void bootLoad( void) @BOOT_START
{ // ensure a jump to bootloader init is placed at BOOT_START
#asm
        PAGESEL     (start_initialization)
        goto        (start_initialization)&0x7ff
#endasm
}

void runApp( void)
{ // run the application
#asm
                PAGESEL     APP_START
                goto        APP_START&0x7FF
#endasm
}

/**************************************************************************
Protocol Description.

    Protocol is a typical master-slave communication protocol, where
    master (PC) sends commands and slave (bootloader equipped device) executes
    them and acknowledges execution.

    * Command format.

    <CMD_CODE> <ADDRESS> <COUNT> <DATA[0..COUNT-1]>
    ---- 2 ---|--- 2 ---|-- 2 --|----- COUNT ------|
     data[0]    data[1]  data[2]     data[3]
 *
    CMD_CODE - Command index (TCmd).
               Length: 2 byte. Mandatory.
    ADDRESS  - Address field. Flash start address for
               CMD_CODE command operation.
               Length: 2 bytes. Optional (command specific).
    COUNT    - Count field. Amount of data/blocks for
               CMD_CODE command operation.
               Length: 2 bytes. Optional (command specific).
    DATA     - Data array.
               Length: COUNT bytes. Optional (command specific).
               Length: X bytes. Optional (command specific).

    Some commands do not utilize all of these fields.
    See 'Command Table' below for details on specific command's format.

    * Command Table.
     --------------------------+---------------------------------------------
    |       Description        |                   Format                    |
    | Synchronize with PC tool |                  <cmdSYNC>                  |
    | Send bootloader info     |                  <cmdINFO>                  |
    | Go to bootloader mode    |                  <cmdBOOT>                  |
    | Restart MCU              |                  <cmdREBOOT>                |
    | Write to MCU flash       | <cmdWRITE><START_ADDR><DATA_LEN><DATA_ARRAY>|
    | Erase MCU flash.         | <cmdERASE><START_ADDR><ERASE_BLOCK_COUNT>   |
     -------------------------------------------------------------------------

     * Acknowledge format.

    Read
    * <CMD_CODE> or
    |---- 2 ----|
        data [0]
 *
    CMD_CODE - Index of command (TCmd) we want to acknowledge.
               Length: 2 byte. Mandatory.

    See 'Acknowledgement Table' below for details on specific command's
    acknowledgement process.

    * Acknowledgement Table.
     --------------------------+---------------------------------------------------
    |       Description        |                   Acknowledgement                 |
    |--------------------------+---------------------------------------------------|
    | Synchronize with PC tool |                  upon reception                   |
    | Send bootloader info     |          no acknowledge, just send info           |
    | Go to bootloader mode    |                  upon reception                   |
    | Restart MCU              |                  no acknowledge                   |
    | Write to MCU flash       | upon each write of internal buffer data to flash  |
    | Erase MCU flash.         |                  upon execution                   |

*************************************************************************************/
// I2C masks
#define I2C_DEV_ADD  0x90    // unique I2C address
#define I2C_ADD_MASK 0xFE    // only address bits
#define I2C_RW_MASK  0x01    // only direction bit

// states
#define S_READ      1       // reading data from device
#define S_WRITE     0       // writing data to device

// BL commands
#define cmdSYNC         1
#define cmdINFO         2
#define cmdBOOT         3
#define cmdREBOOT       4
#define cmdWRITE        11
#define cmdERASE        21

// Supported MCU families/types.
//enum { PC16 = 1, PIC18 = 2, PIC18FJ = 3, PIC24 = 4,  dsPIC = 10, PIC32' = 20;)  dMcuType ;
#define mcuPIC16    1

// data buffers
uint16_t data[ 64];       //  data buffer


/**
 * Write a block of data to flash
 * @param add       address (16-bit unsigned)
 * @param count     number of words
 * @param data      arrray of words
 */
void write( uint16_t add, uint16_t count, uint16_t* data)
{
    // write latches
    while( count-- > 1)
    {
        FLASH_write( add++, *data++, 1);    // latch
    }
    // write last word and entire row
    FLASH_write( add, *data++, 0);          // write
}


void I2C_Initialize( void)
{
    // I2C Initialization
      SSPMSK = I2C_ADD_MASK;        // set the mask bits
      SSPADD = I2C_DEV_ADD;         // set the device address
      SSPCON1 = 0b00100110;         // I2C enabled, 7-bit SLAVE
      SSPCON2bits.SEN = 1;          // enable strech on receive
      //SSPCON3bits.SDAHT = 1;        // extend SDA hold to 300ns
      SSP1IF = 0;                   // clear interrupt flag
      SSP1IE = 0;                   // enable I2C interrupts
}


// macro to send output to buffer (word by word)
#define putw(w)    *w_p++ = ( w);

void I2CSM( void)
{
    uint8_t cmd;                    // command
    static uint16_t *w_p;            // pointer to buffer (words)
    static uint8_t *s_p;             // pointer to buffer (byte)
    static uint16_t s_count;         // keep track of buffer usage

    // I2C state machine
    SSP1IF = 0;                     // clear flag

    if ( SSPSTATbits.D_nA)          // address or data
    {
        if ( SSPSTATbits.R_nW)           // data read/write
        {
            // R = 1-> reading data from device buffer
            if ( s_count-- > 0)           // if a (long) reply was prepared
                SSP1BUF = *s_p++;       // return one byte at a time
            else
                SSP1BUF = 0;            // return 0 in case of error (overflow)
        }
        else
        {
            // W = 0-> writing data to device buffer
            if ( s_count < sizeof( data))
            {
                *s_p++ = SSP1BUF;             // buffer data
                s_count++;
            }
        }
    }

    else                        // address was received -> start a new sequence
    {
        SSPCON1bits.SSPOV = 0;          // clear overflow conditions

        s_p = (uint8_t*)data;           // init buffer pointer

        // separate read from write
        if ( SSPSTATbits.R_nW)          // I2C read command
        {
            // interpret command and prepare for reading, return <cmd> or error <0>
            if ( s_count >= 2)
            {
                cmd = data[0];
                switch( cmd){
                    case cmdSYNC:           // synchronize
//                            ack( cmdSYNC);      // acknowledge immediately
                        break;
                    case cmdBOOT:           // stay in bootloader mode
//                            ack( cmdBOOT);
                        break;
                    case cmdINFO:           // return info record
                        w_p = data;                             // init pointer
                        putw( 38);                              // 2, info block size in bytes
                        putw( 1);    putw( mcuPIC16);           // 4, mcuType
                        putw( 8);    putw( FLASH_SIZE);         // 4, total amount of flash available
                        putw( 3);    putw( FLASH_ROWSIZE );     // 4, erase page size
                        putw( 4);    putw( FLASH_ROWSIZE );     // 4, write row size
                        putw( 5);    putw( 0x0100);             // 4, bootloader revision 0.1
                        putw( 6);    putw( BOOT_START);         // 4, bootloader start address
                        putw( 7);                               // 12, text
                        //    Bu              ck           _C            li          ck
                        putw(0x7542); putw(0x6b63); putw(0x4320); putw(0x696c); putw(0x6b63);
                        s_count = 38;
                        s_p = (uint8_t*)data;
                        break;
                    case cmdREBOOT:         // run application
                        runApp();
                        break;
                    case cmdERASE:          // erase block
                        FLASH_erase( data[1]);
//                            ack( cmdERASE);
                        break;
                    case cmdWRITE:          // write block
                        write( data[1], data[2], &data[3]);
//                            ack( cmdWRITE);
                        break;
                    default:
                        bootLoad();         // restart bootloader (avoid/keep from optimizer)
                        break;
                } // swtich
                SSP1BUF = cmd;          // acknowledge command
            } // if comand
            else
                SSP1BUF = 0;            // error read command sent before any write

        } // I2C read sequence started
        else
        { // I2C write command sequence started
            cmd = SSP1BUF;
            s_count = 0;

        }
    } // new address / sequence started

    SSPCON1bits.CKP = 1;            // release SCL
} // I2C state machine


void main(void)
{
    SYSTEM_Initialize();
    I2C_Initialize();
    while( !TMR0_HasOverflowOccured());     // wait for 1ms

    // check CS if not active (high) -> run the app
    if ( P_CS_GetValue())
    {
        P_LED_SetLow();
        runApp();
    }

    // if CS is active (low) -> boot
    while( 1)
    {
        // poll I2C
        if ( SSP1IF)
        {
            I2CSM();            // serve the I2C state machine
            P_LED_Toggle();     // signal data transfer
        }
    } // main loop
} // main


