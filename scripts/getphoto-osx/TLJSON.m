//
//  TLJSON.m
//  getphoto-osx
//
//  Created by Nathan Vander Wilt on 12/31/10.
//  Copyright 2010 &yet. All rights reserved.
//

#import "TLJSON.h"


@implementation TLJSON

+ (NSString*)stringify:(id)object {
    // TODO: detect cyclic structures
    // TODO: support pretty indent
    
    if ([object isKindOfClass:[NSDictionary class]]) {
        NSMutableString* string = [NSMutableString stringWithString:@"{"];
        BOOL started = NO;
        for (NSString* key in object) {
            if (started) {
                [string appendString:@", "];
            } else {
                started = YES;
            }
            NSString* value = [self stringify:[object valueForKey:key]];
            [string appendFormat:@"\"%@\" : %@", key, value];
        }
        [string appendString:@"}"];
        return string;
    } else if ([object isKindOfClass:[NSArray class]]) {
        NSMutableString* string = [NSMutableString stringWithString:@"["];
        BOOL started = NO;
        for (NSObject* item in object) {
            if (started) {
                [string appendString:@", "];
            } else {
                started = YES;
            }
            NSString* value = [self stringify:item];
            [string appendString:value];
        }
        [string appendString:@"]"];
        return string;
    } else if (object == [NSNull null]) {
        return @"null";
    } else if (CFGetTypeID((CFTypeRef)object) == CFBooleanGetTypeID()) {
        // http://www.cocoabuilder.com/archive/cocoa/287795-boolean-values-in-plist.html
        return ([object boolValue]) ? @"true" : @"false";
    } else if ([object isKindOfClass:[NSNumber class]]) {
        return [object stringValue];
    } else if ([object isKindOfClass:[NSString class]]) {
        return [NSString stringWithFormat:@"\"%@\"", object];
    } /*else if ([object isKindOfClass:[NSDate class]]) {
        return [object descriptionWithCalendarFormat:@"\"%Y-%m-%dT%H:%M:%S%Z\""];
    }  */
    NSParameterAssert([object isKindOfClass:[TLJSON class]]);
    return nil;
}

@end
