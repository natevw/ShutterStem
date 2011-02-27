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
  //{"original", no_argument, NULL, 'o'},       // output _attachments/original
  //{"modified", no_argument, NULL, 'O'},       // output _attachments/modified (original format with modidata)
    {"export", required_argument, NULL, 'e'},   // output _attachments/export/SIZE|original_size.jpg (modidata modifying metadata)
    {"thumbnail", required_argument, NULL, 't'},// output _attachments/thumbnail/SIZE.jpg (only modidata metadata)
  //{"modidata", required_argument, NULL, 'M'}, // (re)set or remove {"timestamp":"2010-02-18T20:15:00-08:00","location":null}
    {"metadata", optional_argument, NULL, 'm'}, // output original's ["timestamp","location","etc."] in document (or whatever's interesting)
    {"suffix", optional_argument, NULL, 'x'},   // make duplicated attachment name unique using given suffix (otherwise overwrites)
    {"timezone", optional_argument, NULL, 'z'}, // timezone used to read/write timestamps, defaults to system
    {}
};

typedef enum { log_warning, log_error, log_fatal } log_type;
void json_log(log_type type, const char* message_fmt, ...) {
    va_list args;
    va_start(args, message_fmt);
    fprintf(stderr, "{\"error\":%s, \"message\":\"", (type > log_warning) ? "true" : "false");
    vfprintf(stderr, message_fmt, args);
    fprintf(stderr, "\"}\n");
    if (type == log_fatal) {
        exit(1);
    }
}

int main(int argc, char* argv[]) {
    // Node.js encodes args as UTF-8: https://github.com/ry/node/blob/master/src/node_child_process.cc
    // Python seems to just dump the raw "binary" strs? http://stackoverflow.com/questions/1598334/ http://bugs.python.org/issue1759845
    
    NSAutoreleasePool* pool = [NSAutoreleasePool new];
    
    NSString* imagePath = nil;
    if (argc < 2) {
        json_log(log_fatal, "No photo file given.");
    }
    imagePath = [NSString stringWithUTF8String:argv[optind++]];
    
    NSMutableDictionary* imageDoc = [NSMutableDictionary dictionary];
    CGImageSourceRef imgSrc = CGImageSourceCreateWithURL((CFURLRef)[NSURL fileURLWithPath:imagePath isDirectory:NO] , NULL);
    if (!imgSrc) {
        json_log(log_fatal, "Could not open file.");
    }
    CFStringRef imgUTI = CGImageSourceGetType(imgSrc);
    if (imgUTI) {
        NSMutableDictionary* typeInfo = [NSMutableDictionary dictionary];
        NSString* contentType = [(id)UTTypeCopyPreferredTagWithClass(imgUTI, kUTTagClassMIMEType) autorelease];
        if (contentType) {
            [typeInfo setObject:contentType forKey:@"type"];
        }
        [typeInfo setObject:(id)imgUTI forKey:@"uti"];
        [imageDoc setObject:typeInfo forKey:@"original_info"];
    } else {
        json_log(log_fatal, "Unsupported file type.");
    }
    NSMutableDictionary* thumbnailOptions = [NSMutableDictionary dictionaryWithObjectsAndKeys:
                                             (id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailFromImageAlways,
                                             (id)kCFBooleanTrue, (id)kCGImageSourceCreateThumbnailWithTransform,
                                             (id)kCFBooleanTrue, (id)kCGImageSourceShouldCache, nil];
    
    NSString* suffix = @"";
    NSTimeZone* tz = [NSTimeZone defaultTimeZone];

    while (1) {
        int opt = getopt_long(argc, argv, "", cli_options, NULL);
        if (opt == -1) {
            break;
        } else if (opt == 'x') {
            if (optarg) {
                suffix = [NSString stringWithUTF8String:optarg];
            } else {
                suffix = @"";
            }
        } else if (opt == 'z') {
            if (optarg) {
                NSString* zoneName = [NSString stringWithUTF8String:optarg];
                tz = [NSTimeZone timeZoneWithName:zoneName];
            } else {
                tz = [NSTimeZone defaultTimeZone];
            }
        } else if (opt == 't' || opt == 'e') {  // add JPEG thumbnail or export to imageDoc
            long size = 0;
            if (optarg) {
                size = strtol(optarg, NULL, 10);
                if (size < 0 || size == 1 || size > 8192) {
                    json_log(log_error, "Invalid thumbnail size: %li", size);
                    continue;
                }
                
            }
            if (size) {
                [thumbnailOptions setObject:[NSNumber numberWithLong:size] forKey:(id)kCGImageSourceThumbnailMaxPixelSize];
            } else {
                [thumbnailOptions removeObjectForKey:(id)kCGImageSourceThumbnailMaxPixelSize];
            }
            
            NSString* nameType = (opt == 't') ? @"thumbnail" : @"export";
            NSString* nameSize = (size) ? [NSString stringWithFormat:@"%li", size] : @"original_size";
            NSString* attachmentName = [NSString stringWithFormat:@"%@/%@%@.jpg", nameType, nameSize, suffix];
            
            CGImageRef img = CGImageSourceCreateThumbnailAtIndex(imgSrc, 0, (CFDictionaryRef)thumbnailOptions);
            if (!img) {
                json_log(log_error, "Could not create thumbnail!");
                continue;
            }
            
            NSMutableData* jpegData = [NSMutableData data];
            CGImageDestinationRef imgDst = CGImageDestinationCreateWithData((CFMutableDataRef)jpegData, kUTTypeJPEG, 1, NULL);
            if (opt == 't') {
                CGImageDestinationAddImage(imgDst, img, NULL);
            } else {
                NSDictionary* origMetadata = [(id)CGImageSourceCopyPropertiesAtIndex(imgSrc, 0, NULL) autorelease];
                NSMutableDictionary* modMetadata = nil;
                NSLog(@"%@", origMetadata);
                if ([[origMetadata objectForKey:(id)kCGImagePropertyOrientation] intValue] > 1) {
                    modMetadata = [[origMetadata mutableCopy] autorelease];
                    [modMetadata setObject:[NSNumber numberWithInt:1] forKey:(id)kCGImagePropertyOrientation];
                    
                    NSDictionary* tiffData = [origMetadata objectForKey:(id)kCGImagePropertyTIFFDictionary];
                    if ([[tiffData objectForKey:(id)kCGImagePropertyTIFFOrientation] intValue] > 1) {
                        NSMutableDictionary* newTiffData = [[tiffData mutableCopy] autorelease];
                        [newTiffData setObject:[NSNumber numberWithInt:1] forKey:(id)kCGImagePropertyTIFFOrientation];
                        [modMetadata setObject:newTiffData forKey:(id)kCGImagePropertyTIFFDictionary];
                    }
                }
                // TODO: modify origMetadata according to modidata
                if (modMetadata) {
                    CGImageDestinationAddImage(imgDst, img, (CFDictionaryRef)modMetadata);
                } else {
                    CGImageDestinationAddImage(imgDst, img, (CFDictionaryRef)origMetadata);
                }
            }
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
            [attachments setObject:thumbnail forKey:attachmentName];
            
            CGImageRelease(img);
        } else if (opt == 'm') {
            if (optarg) {
                json_log(log_warning, "Metadata filtering not implemented, including default fields instead.");
            }
            
            NSDictionary* info = [(id)CGImageSourceCopyPropertiesAtIndex(imgSrc, 0, NULL) autorelease];
            NSDictionary* exif = [info valueForKey:(id)kCGImagePropertyExifDictionary];
            
            NSString* timestamp = [exif valueForKey:(id)kCGImagePropertyExifDateTimeOriginal];
            if (timestamp) {
                NSDateFormatter* tiffFormat = [NSDateFormatter tl_tiffDateFormatter];
                [tiffFormat setTimeZone:tz];
                NSDate* date = [tiffFormat dateFromString:timestamp];
                NSString* dateString = [NSDateFormatter tl_dateToRFC3339:date withTimezone:tz];
                [imageDoc setObject:dateString forKey:@"timestamp"];
            } else {
                json_log(log_warning, "No timestamp found!");
            }
            
            // TODO: camera, lens, exposure, location info
        }
    }
    
    CFRelease(imgSrc);
    
    printf("%s\n", [[TLJSON stringify:imageDoc] UTF8String]);
    
    [pool drain];
    return 0;
}
