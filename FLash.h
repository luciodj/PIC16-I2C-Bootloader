/*
 * Flash.h
 *
 * Updated on November 4, 2014
 */
#define FLASH_SIZE      8192        // 8K bytes

#define FLASH_ROWSIZE   32          // size of a row in words

#define FLASH_ROWMASK     FLASH_ROWSIZE-1   

/******************************************************************************
 * Generic Flash functions
 */

 /**
 * Read a word from program Flash memory
 *
 * @param address   source address (absolute FLASH memory address)
 * @return          word retrieved from FLASH memory
 */
unsigned FLASH_read( unsigned address);


/**
 * Read a word from configuration Flash memory
 *
 * @param address   source address (absolute FLASH memory address)
 * @return          word retrieved from FLASH memory
 */
unsigned FLASH_readConfig( unsigned address);

/**
 * Read a block of words from program Flash memory
 *
 * @param buffer    destination buffer (must be sufficiently large)
 * @param address   source address (absolute FLASH memory address)
 * @param count     number of words to be retrieved
 */
void    FLASH_readBlock( unsigned* buffer, unsigned address, char count);


/**
 * Write a word of data to Flash memory (latches)
 *  an actual write is performed only if LWLO = 0, data is latched if LWLO = 1
 *
 * @param address   destination address (absolute flash memory)
 * @param data      word of data to be written (latched)
 * @param latch     1 = latch, 0 = write
 */
void    FLASH_write( unsigned address, unsigned data, char latch);


/**
 * Erase a row of Flash memory
 *
 * @param address   absolute address in Flash contained in selected row
 */
void    FLASH_erase( unsigned address);


