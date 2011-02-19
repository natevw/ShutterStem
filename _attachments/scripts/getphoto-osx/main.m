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
#import "TLJSON.h"
#import "NSDateFormatter+TLExtensions.h"


static const struct option cli_options[] = {
    {"original", no_argument, NULL, 'o'},       // output _attachments/original
    {"modified", no_argument, NULL, 'O'},       // output _attachments/modified (with "write" metadata when given)
    {"export", required_argument, NULL, 'e'},   // output _attachments/export/SIZE.jpg (with "write" metadata if given)
    {"thumbnail", required_argument, NULL, 't'},// output _attachments/thumbnail/SIZE.jpg (with no metadata)
    {"metadata", required_argument, NULL, 'm'}, // {"read":["timestamp","location"], "write":{"timestamp":"2010-02-18T20:15:00-08:00"}}
    {"timezone", required_argument, NULL, 'z'}, // timezone used to read/write timestamps, defaults to system
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
    
    NSDictionary* info = (id)CGImageSourceCopyPropertiesAtIndex(imgSrc, 0, NULL);
    [info autorelease];
    
    NSString* timestamp = [[info valueForKey:(id)kCGImagePropertyExifDictionary] valueForKey:(id)kCGImagePropertyExifDateTimeOriginal];
    if (!timestamp) {
        fprintf(stderr, "No timestamp found\n");
        exit(-1);
    }
    
    NSDateFormatter* tiffFormat = [NSDateFormatter tl_tiffDateFormatter];
    [tiffFormat setTimeZone:tz];
    NSDate* date = [tiffFormat dateFromString:timestamp];
    NSString* dateString = [NSDateFormatter tl_dateToRFC3339:date withTimezone:tz];
    [imageDoc setObject:dateString forKey:@"timestamp"];
    
    NSMutableDictionary* thumbnailOptions = [NSMutableDictionary dictionaryWithObjectsAndKeys:(id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailFromImageAlways, (id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailWithTransform, nil];
    if ([thumbnails count] > 1) {
        [thumbnailOptions setObject:(id)kCFBooleanTrue forKey:(id)kCGImageSourceShouldCache];
    }
    for (NSNumber* size in thumbnails) {
        [thumbnailOptions setObject:size forKey:(id)kCGImageSourceThumbnailMaxPixelSize];
        CGImageRef img = CGImageSourceCreateThumbnailAtIndex(imgSrc, 0, (CFDictionaryRef)thumbnailOptions);
        
        NSMutableData* jpegData = [NSMutableData data];
        CGImageDestinationRef imgDst = CGImageDestinationCreateWithData((CFMutableDataRef)jpegData, kUTTypeJPEG, 1, NULL);
        CGImageDestinationAddImage(imgDst, img, NULL);
        CGImageDestinationFinalize(imgDst);
        CFRelease(imgDst);
        
        NSMutableDictionary* thumbnail = [NSMutableDictionary dictionaryWithCapacity:2];
        [thumbnail setObject:@"image/jpeg" forKey:@"content_type"];
        [thumbnail setObject:[jpegData tl_base64EncodedString] forKey:@"data"];
        
        NSMutableDictionary* attachments = [imageDoc objectForKey:@"_attachments"];
        if (!attachments) {
            attachments = [NSMutableDictionary dictionary];
            [imageDoc setObject:attachments forKey:@"_attachments"];
        }
        NSString* thumbnailName = [NSString stringWithFormat:@"thumbnail/%lu.jpg", [size unsignedLongValue]];
        [attachments setObject:thumbnail forKey:thumbnailName];
        
        CGImageRelease(img);
    }
    
    CFRelease(imgSrc);
    
    printf("%s\n", [[TLJSON stringify:imageDoc] UTF8String]);
    
    [pool drain];
    return 0;
}
