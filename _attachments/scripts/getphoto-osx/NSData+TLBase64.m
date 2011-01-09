//
//  NSData+TLBase64.m
//  getphoto-osx
//
//  Created by Nathan Vander Wilt on 12/31/10.
//

/*
 Based on http://cocoawithlove.com/2009/06/base64-encoding-options-on-mac-and.html
 See also http://www.dribin.org/dave/blog/archives/2006/03/12/base64_cocoa/
 
 Copyright 2009 Matt Gallagher. All rights reserved.
 
 Permission is given to use this source code file, free of charge, in any project, commercial or otherwise,
 entirely at your risk, with the condition that any redistribution (in part or whole) of source code must retain
 this copyright and permission notice. Attribution in compiled projects is appreciated but not required.
 */

#import "NSData+TLBase64.h"


#include <openssl/bio.h>
#include <openssl/evp.h>

#define BUFFSIZE 256


@implementation NSData (TLBase64)

+ (NSData*)tl_dataByBase64DecodingString:(NSString*)encodedData {
    encodedData = [encodedData stringByAppendingString:@"\n"];
    NSData* data = [encodedData dataUsingEncoding:NSASCIIStringEncoding];
    
    // Construct an OpenSSL context
    BIO* context = BIO_new_mem_buf((void*)[data bytes], [data length]);
    
    // Tell the context to encode base64
    BIO* command = BIO_new(BIO_f_base64());
    context = BIO_push(command, context);
    
    // Encode all the data
    NSMutableData* outputData = [NSMutableData data];
    
    int len;
    char inbuf[BUFFSIZE];
    while ((len = BIO_read(context, inbuf, BUFFSIZE)) > 0) {
        [outputData appendBytes:inbuf length:len];
    }
    
    BIO_free_all(context);
    [data self]; // extend GC lifetime of data to here
    
    return outputData;
}

- (NSString*)tl_base64EncodedString {
    // Construct an OpenSSL context
    BIO* context = BIO_new(BIO_s_mem());
    
    // Tell the context to encode base64
    BIO* command = BIO_new(BIO_f_base64());
    context = BIO_push(command, context);
    
    // Encode all the data
    BIO_write(context, [self bytes], [self length]);
    BIO_flush(context);
    
    // Get the data out of the context
    char* outputBuffer;
    long outputLength = BIO_get_mem_data(context, &outputBuffer);
    NSString* encodedString = [[NSString alloc] initWithBytes:outputBuffer length:outputLength encoding:NSASCIIStringEncoding];
    BIO_free_all(context);
    
    NSString* noNewlines = [encodedString stringByReplacingOccurrencesOfString:@"\n" withString:@""];
    [encodedString release];
    return noNewlines;
}


@end
