/*
# -*- coding: utf-8 -*-
#
# AlterX GUI - ascope - linuxcnc rt component for oscilloscope
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
*/

#define RTAPI

#include <rtapi.h>		/* RTAPI realtime OS API */
#include <rtapi_app.h>		/* RTAPI realtime module decls */
#include <hal.h>		/* HAL public API decls */
#include <stdio.h>	
#include <rtapi_string.h>
#include <rtapi_stdint.h>
#include <rtapi_common.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define SHMPTR(offset)  ( (void *)( hal_shmem_base + (offset) ) )
#define SHMOFF(ptr)     ( ((char *)(ptr)) - hal_shmem_base )
                       
typedef union {
    hal_bit_t b;
    hal_s32_t s;
    hal_u32_t u;
    hal_float_t f;
} hal_data_u;

typedef struct {
    int next;			/* next element in list */
    int prev;			/* previous element in list */
} hal_list_t;

typedef struct {
    int version;		/* version code for structs, etc */
    unsigned long mutex;	/* protection for linked lists, etc. */
    hal_s32_t shmem_avail;	/* amount of shmem left free */
    constructor pending_constructor;
			/* pointer to the pending constructor function */
    char constructor_prefix[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    char constructor_arg[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    int shmem_bot;		/* bottom of free shmem (first free byte) */
    int shmem_top;		/* top of free shmem (1 past last free) */
    int comp_list_ptr;		/* root of linked list of components */
    int pin_list_ptr;		/* root of linked list of pins */
    int sig_list_ptr;		/* root of linked list of signals */
    int param_list_ptr;		/* root of linked list of parameters */
    int funct_list_ptr;		/* root of linked list of functions */
    int thread_list_ptr;	/* root of linked list of threads */
    long base_period;		/* timer period for realtime tasks */
    int threads_running;	/* non-zero if threads are started */
    int oldname_free_ptr;	/* list of free oldname structs */
    int comp_free_ptr;		/* list of free component structs */
    int pin_free_ptr;		/* list of free pin structs */
    int sig_free_ptr;		/* list of free signal structs */
    int param_free_ptr;		/* list of free parameter structs */
    int funct_free_ptr;		/* list of free function structs */
    hal_list_t funct_entry_free;	/* list of free funct entry structs */
    int thread_free_ptr;	/* list of free thread structs */
    int exact_base_period;      /* if set, pretend that rtapi satisfied our
				   period request exactly */
    unsigned char lock;         /* hal locking, can be one of the HAL_LOCK_* types */
} hal_data_t;

typedef struct {
    int next_ptr;		/* next pin in linked list */
    int data_ptr_addr;		/* address of pin data pointer */
    int owner_ptr;		/* component that owns this pin */
    int signal;			/* signal to which pin is linked */
    hal_data_u dummysig;	/* if unlinked, data_ptr points here */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_pin_dir_t dir;		/* pin direction */
    char name[HAL_NAME_LEN + 1];	/* pin name */
} hal_pin_t;

typedef struct {
    int next_ptr;		/* next signal in linked list */
    int data_ptr;		/* offset of signal value */
    hal_type_t type;		/* data type */
    int readers;		/* number of input pins linked */
    int writers;		/* number of output pins linked */
    int bidirs;			/* number of I/O pins linked */
    char name[HAL_NAME_LEN + 1];	/* signal name */
} hal_sig_t;

typedef struct {
    int next_ptr;		/* next parameter in linked list */
    int data_ptr;		/* offset of parameter value */
    int owner_ptr;		/* component that owns this signal */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_param_dir_t dir;	/* data direction */
    char name[HAL_NAME_LEN + 1];	/* parameter name */
} hal_param_t;

enum CMD {
    OSC_STOP,
    OSC_LIST,
    OSC_STATE,
    OSC_CHANNEL,
    OSC_TRIG,
    OSC_RUN,
    OSC_CHECK,
    OSC_GET
};

enum TRIG {
    SAMPLE_IDLE,
    SAMPLE_RUN,
    SAMPLE_COMPLETE,
    SAMPLE_HIGH,
    SAMPLE_LOW,
    SAMPLE_CHANGE
};

enum HAL_TYPE {
    HAL_PIN,
    HAL_SIG,
    HAL_PARAMETER
};

typedef struct {
    unsigned int cmd:8;
    unsigned int type:8;
    hal_data_u value;
} socket_req_t;

typedef struct {
    int type;
    int offset;
} channels_t;

typedef struct {
    int cmd;
    int type;
    int pin;
    float value;
    hal_data_u last;
} trigger_t;

typedef struct {
    unsigned int channel:8;
    unsigned int type:8;
    hal_data_u value;
} data_t;

typedef struct {
    pthread_mutex_t* mutex;
    socket_req_t* request;
    channels_t* channels;
    trigger_t* trigger;
    data_t* array;
    int* pointer;
} thread_arg_t;

extern char *hal_shmem_base;

void connection_handler(void *arg);
static void sample(void *arg, long period);
void set_data_value(int type, void *valptr, data_t *structptr);
static char *get_data_value(int type, void *valptr);
int need_quit(pthread_mutex_t *mtx);
