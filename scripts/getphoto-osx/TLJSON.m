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
    return [self stringify:object indent:0];
}

+ (NSString*)stringify:(id)object indent:(NSUInteger)indentAmount {
    // TODO: detect cyclic structures
    (void)indentAmount;
    
    if ([object isKindOfClass:[NSDictionary class]]) {
        // TODO: implement
    } else if ([object isKindOfClass:[NSArray class]]) {
        // TODO: implement
    } else if (object == [NSNull null]) {
        return @"null";
    } else if (CFGetTypeID((CFTypeRef)object) == CFBooleanGetTypeID()) {
        // http://www.cocoabuilder.com/archive/cocoa/287795-boolean-values-in-plist.html
        return ([object boolValue]) ? @"true" : @"false";
    } else if ([object isKindOfClass:[NSNumber class]]) {
        return [object stringValue];
    } else if ([object isKindOfClass:[NSString class]]) {
        return [NSString stringWithFormat:@"\"%@\"", object];
    } else if ([object isKindOfClass:[NSDate class]]) {
        return [object descriptionWithCalendarFormat:@"\"%Y-%m-%dT%H:%M:%S%Z\""];
    }
    return nil;
}

@end
