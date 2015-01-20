/**
  @Generated Pin Manager Header File

  @Company:
    Microchip Technology Inc.

  @File Name:
    pin_manager.h

  @Summary:
    This is the Pin Manager file generated using MPLAB® Code Configurator

  @Description:
    This header file provides implementations for pin APIs for all pins selected in the GUI.
    Generation Information :
        Product Revision  :  MPLAB® Code Configurator - v2.10
        Device            :  PIC16F1783
        Version           :  1.01
    The generated drivers are tested against the following:
        Compiler          :  XC8 v1.33
        MPLAB             :  MPLAB X 2.26
*/

/*
Copyright (c) 2013 - 2014 released Microchip Technology Inc.  All rights reserved.

Microchip licenses to you the right to use, modify, copy and distribute
Software only when embedded on a Microchip microcontroller or digital signal
controller that is integrated into your product or third party product
(pursuant to the sublicense terms in the accompanying license agreement).

You should refer to the license agreement accompanying this Software for
additional information regarding your rights and obligations.

SOFTWARE AND DOCUMENTATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION, ANY WARRANTY OF
MERCHANTABILITY, TITLE, NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
IN NO EVENT SHALL MICROCHIP OR ITS LICENSORS BE LIABLE OR OBLIGATED UNDER
CONTRACT, NEGLIGENCE, STRICT LIABILITY, CONTRIBUTION, BREACH OF WARRANTY, OR
OTHER LEGAL EQUITABLE THEORY ANY DIRECT OR INDIRECT DAMAGES OR EXPENSES
INCLUDING BUT NOT LIMITED TO ANY INCIDENTAL, SPECIAL, INDIRECT, PUNITIVE OR
CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA, COST OF PROCUREMENT OF
SUBSTITUTE GOODS, TECHNOLOGY, SERVICES, OR ANY CLAIMS BY THIRD PARTIES
(INCLUDING BUT NOT LIMITED TO ANY DEFENSE THEREOF), OR OTHER SIMILAR COSTS.
*/

#ifndef PIN_MANAGER_H
#define PIN_MANAGER_H

#define INPUT   1
#define OUTPUT  0

#define HIGH    1
#define LOW     0

#define ANALOG      1
#define DIGITAL     0

#define PULL_UP_ENABLED      1
#define PULL_UP_DISABLED     0

// get/set P_CS aliases
#define P_CS_TRIS               TRISA5
#define P_CS_LAT                LATA5
#define P_CS_PORT               RA5
#define P_CS_WPU                WPUA5
#define P_CS_ANS                ANSA5
#define P_CS_SetHigh()    do { LATA5 = 1; } while(0)
#define P_CS_SetLow()   do { LATA5 = 0; } while(0)
#define P_CS_Toggle()   do { LATA5 = ~LATA5; } while(0)
#define P_CS_GetValue()         RA5
#define P_CS_SetDigitalInput()    do { TRISA5 = 1; } while(0)
#define P_CS_SetDigitalOutput()   do { TRISA5 = 0; } while(0)

#define P_CS_SetPullup()    do { WPUA5 = 1; } while(0)
#define P_CS_ResetPullup()   do { WPUA5 = 0; } while(0)
#define P_CS_SetAnalogMode()   do { ANSA5 = 1; } while(0)
#define P_CS_SetDigitalMode()   do { ANSA5 = 0; } while(0)
// get/set P_LED aliases
#define P_LED_TRIS               TRISA7
#define P_LED_LAT                LATA7
#define P_LED_PORT               RA7
#define P_LED_WPU                WPUA7
#define P_LED_ANS                ANSA7
#define P_LED_SetHigh()    do { LATA7 = 1; } while(0)
#define P_LED_SetLow()   do { LATA7 = 0; } while(0)
#define P_LED_Toggle()   do { LATA7 = ~LATA7; } while(0)
#define P_LED_GetValue()         RA7
#define P_LED_SetDigitalInput()    do { TRISA7 = 1; } while(0)
#define P_LED_SetDigitalOutput()   do { TRISA7 = 0; } while(0)

#define P_LED_SetPullup()    do { WPUA7 = 1; } while(0)
#define P_LED_ResetPullup()   do { WPUA7 = 0; } while(0)
#define P_LED_SetAnalogMode()   do { ANSA7 = 1; } while(0)
#define P_LED_SetDigitalMode()   do { ANSA7 = 0; } while(0)

/**
 * @Param
    none
 * @Returns
    none
 * @Description
    GPIO and peripheral I/O initialization
 * @Example
    PIN_MANAGER_Initialize();
 */
void PIN_MANAGER_Initialize (void);

/**
 * @Param
    none
 * @Returns
    none
 * @Description
    Interrupt on Change Handling routine
 * @Example
    PIN_MANAGER_IOC();
 */
void PIN_MANAGER_IOC(void);

#endif // PIN_MANAGER_H
/**
 End of File
*/