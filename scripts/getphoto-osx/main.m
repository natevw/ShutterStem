/*
 *  main.c
 *  getphoto-osx
 *
 *  Created by Nathan Vander Wilt on 12/31/10.
 *  Copyright 2010 Calf Trail Software, LLC. All rights reserved.
 *
 */

#include <Foundation/Foundation.h>
#include <ApplicationServices/ApplicationServices.h>

#include <getopt.h>
#import "NSData+TLBase64.h"


static const struct option cli_options[] = {
    {"thumbnail", required_argument, NULL, 't'},
    {"timezone", required_argument, NULL, 'z'},
    {}
};

int main(int argc, char* argv[]) {
    NSAutoreleasePool* pool = [NSAutoreleasePool new];
    
    
    NSMutableArray* thumbnails = [NSMutableArray array];
    NSTimeZone* tz = [NSTimeZone defaultTimeZone];
    while (1) {
        int opt = getopt_long(argc, argv, "", cli_options, NULL); //&option_index);
        if (opt == -1) {
            break;
        } else if (opt == 't') {
            long size = strtol(optarg, NULL, 10);
            if (size < 1 || size > 8192) {
                fprintf(stderr, "Invalid thumbnail size\n");
                exit(-1);
            }
            [thumbnails addObject:[NSNumber numberWithLong:size]];
        }  else if (opt == 'z') {
            // Node.js encodes args as UTF-8: https://github.com/ry/node/blob/master/src/node_child_process.cc
            NSString* zoneName = [NSString stringWithUTF8String:optarg];
            tz = [NSTimeZone timeZoneWithName:zoneName];
        }
    }
    
    NSString* file = nil;
    if (optind < argc) {
        file = [NSString stringWithUTF8String:argv[optind]];
    } else {
        fprintf(stderr, "No photo file given\n");
        exit(-1);
    }
    
    
    NSMutableDictionary* imageDoc = [NSMutableDictionary dictionary];
    
    CGImageSourceRef imgSrc = CGImageSourceCreateWithURL((CFURLRef)[NSURL fileURLWithPath:file isDirectory:NO] , NULL);
    
    NSMutableDictionary* thumbnailOptions = [NSMutableDictionary dictionaryWithObjectsAndKeys:(id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailFromImageAlways, (id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailWithTransform, nil];
    for (NSNumber* size in thumbnails) {
        [thumbnailOptions setObject:size forKey:(id)kCGImageSourceThumbnailMaxPixelSize];
        CGImageRef img = CGImageSourceCreateThumbnailAtIndex(imgSrc, 0, (CFDictionaryRef)thumbnailOptions);
        
        NSMutableData* jpegData = [NSMutableData data];
        CGImageDestinationRef imgDst = CGImageDestinationCreateWithData((CFMutableDataRef)jpegData, kUTTypeJPEG, 1, NULL);
        CGImageDestinationAddImage(imgDst, img, NULL);
        CGImageDestinationFinalize(imgDst);
        CFRelease(imgDst);
        
        NSMutableDictionary* thumbnail = [NSMutableDictionary dictionaryWithCapacity:3];
        [thumbnail setObject:@"image/jpeg" forKey:@"content_type"];
        [thumbnail setObject:jpegData forKey:@"data"];
        
        NSMutableDictionary* attachments = [imageDoc objectForKey:@"_attachments"];
        if (!attachments) {
            attachments = [NSMutableDictionary dictionary];
            [imageDoc setObject:attachments forKey:@"_attachments"];
        }
        NSString* thumbnailName = [NSString stringWithFormat:@"thumbnails/%lu.jpg", [size unsignedLongValue]];
        [attachments setObject:thumbnail forKey:thumbnailName];
        
        CGImageRelease(img);
    }
    
    CFRelease(imgSrc);
    
    
    NSLog(@"%@", imageDoc);
    
    [pool drain];
    return 0;
}
