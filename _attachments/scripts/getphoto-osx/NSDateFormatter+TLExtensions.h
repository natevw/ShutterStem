//
//  NSDateFormatter+TLExtensions.h
//
//  Created by Nathan Vander Wilt on 2/20/10.
//  Copyright 2010 Calf Trail Software, LLC. All rights reserved.
//

#import <Cocoa/Cocoa.h>


@interface NSDateFormatter (TLExtensions)

+ (NSDateFormatter*)tl_tiffDateFormatter;

// ISO8601 style dates (should be subclass of NSDateFormatter but whatevs)
+ (NSDate*)tl_dateFromRFC3339:(NSString*)xslDateTime;
+ (NSString*)tl_dateToRFC3339:(NSDate*)date withTimezone:(NSTimeZone*)tz;

@end
