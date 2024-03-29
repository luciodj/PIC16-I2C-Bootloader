/*
 *  File: Flash.c
 *
 *  Self Write Flash support functions
 *
 *  Author: Lucio Di Jasio
 *
 *  Created on November 21, 2014
 */
#include <xc.h>
#include "Flash.h"

/******************************************************************************
 * Generic Flash functions
 */

unsigned FLASH_readConfig( unsigned address)
{
    // 1. load the address pointers
    EEADR = address;
    EECON1bits.CFGS = 1;    // select the configuration flash address space
    EECON1bits.RD = 1;      // next operation will be a read
    NOP();
    NOP();

    // 2. return value read
    return EEDAT;
} // FLASH_config


unsigned FLASH_read( unsigned address)
{
    // 1. load the address pointers
    EEADR = address;
    EECON1bits.CFGS = 0;    // select the flash address space
    EECON1bits.RD = 1;      // next operation will be a read
    NOP();
    NOP();

    // 2. return value read
    return EEDAT;
} // FLASH_read


void FLASH_readBlock( unsigned *buffer, unsigned address, char count)
{
    while ( count > 0)
    {
        *buffer++ = FLASH_read( address++);
        count--;
    }
} // FLASH_readBLock


/**
 * unlock Flash Sequence
 */
void _unlock( void)
{
    #asm
        BANKSEL     EECON2
        MOVLW       0x55
        MOVWF       EECON2 & 0x7F
        MOVLW       0xAA
        MOVWF       EECON2 & 0x7F
        BSF         EECON1 & 0x7F,1    ; set WR bit
        NOP
        NOP
    #endasm
} // unlock


void FLASH_write( unsigned address, unsigned data, char latch)
{
    // 1. disable interrupts (remember setting)
    char temp = INTCONbits.GIE;
    INTCONbits.GIE = 0;

    // 2. load the address pointers
    EEADR = address;
    EEDAT = data;
    EECON1bits.LWLO = latch;// 1 = latch, 0 = write row
    EECON1bits.CFGS = 0;    // de-select the configuration space
    EECON1bits.EEPGD =1;    // select the program flash space (178x!!!)
    EECON1bits.FREE = 0;    // next operation will be a write
    EECON1bits.WREN = 1;    // enable flash memory write/erase

    // 3. perform unlock sequence
    _unlock();

    // 4. restore interrupts
    if ( temp)
        INTCONbits.GIE = 1;

} // FLASH_write


void FLASH_erase( unsigned address)
{
    // 1. disable interrupts (remember setting)
    char temp = INTCONbits.GIE;
    INTCONbits.GIE = 0;

    
    // 2. load the address pointers
    EEADR = address;
    EECON1bits.CFGS = 0;    // deselect the config space
    EECON1bits.EEPGD =1;    // select the flash address space
    EECON1bits.FREE = 1;    // next operation will be an erase
    EECON1bits.WREN = 1;    // enable flash memory write/erase

    // 3. perform unlock sequence and erase
    _unlock();

    // 4. disable writes and restore interrupts
    EECON1bits.WREN = 0;    // disable flash memory write/erase
    if ( temp)
        INTCONbits.GIE = 1;

} // FLASH_erase



