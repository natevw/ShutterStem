//
//  NSDateFormatter+TLExtensions.m
//
//  Created by Nathan Vander Wilt on 2/20/10.
//  Copyright 2010 Calf Trail Software, LLC. All rights reserved.
//

#import "NSDateFormatter+TLExtensions.h"

static const NSUInteger TLYMDHMSCalendarUnit = NSYearCalendarUnit | NSMonthCalendarUnit | NSDayCalendarUnit | NSHourCalendarUnit | NSMinuteCalendarUnit | NSSecondCalendarUnit;


@implementation NSDateFormatter (TLExtensions)

+ (NSDateFormatter*)tl_tiffDateFormatter {
	NSDateFormatter* tiffDateFormatter = [[NSDateFormatter new] autorelease];
	NSCalendar* gregorian = [[NSCalendar alloc] initWithCalendarIdentifier:NSGregorianCalendar];
	[tiffDateFormatter setCalendar:gregorian];
	[gregorian release];
	[tiffDateFormatter setDateFormat:@"yyyy:MM:dd HH:mm:ss"];
	return tiffDateFormatter;
}

+ (NSDate*)tl_dateFromRFC3339:(NSString*)xslDateTime {
	NSCParameterAssert(xslDateTime != nil);
	/* Parse xsd:dateTime http://www.w3.org/TR/xmlschema-2/#dateTime in an accepting manner.
	 '-'? yyyy '-' mm '-' dd 'T' hh ':' mm ':' ss ('.' s+)? ((('+' | '-') hh ':' mm) | 'Z')?
	 Note that yyyy may be negative, or more than 4 digits.
	 When a timezone is added to a UTC dateTime, the result is the date and time "in that timezone". */
	int year = 0;
	unsigned int month = 0, day = 0, hours = 0, minutes = 0;
	double seconds = 0.0;
	char timeZoneBuffer[7] = "";
	int numFieldsParsed = sscanf([xslDateTime UTF8String], "%d-%u-%u T %u:%u:%lf %6s",
								 &year, &month, &day, &hours, &minutes, &seconds, timeZoneBuffer);
	if (numFieldsParsed < 6) {
		return nil;
	}
	
	int timeZoneSeconds = 0;
	if (timeZoneBuffer[0] && timeZoneBuffer[0] != 'Z') {
		int tzHours = 0;
		unsigned int tzMinutes = 0;
		int numTimezoneFieldsParsed = sscanf(timeZoneBuffer, "%d:%ud", &tzHours, &tzMinutes);
		if (numTimezoneFieldsParsed < 2) {
			return nil;
		}
		timeZoneSeconds = 60 * (tzMinutes + (60 * abs(tzHours)));
		if (tzHours < 0) {
			timeZoneSeconds = -timeZoneSeconds;
		}
	}
	
	NSDateComponents* parsedComponents = [[NSDateComponents new] autorelease];
	[parsedComponents setYear:year];
	[parsedComponents setMonth:month];
	[parsedComponents setDay:day];
	[parsedComponents setHour:hours];
	[parsedComponents setMinute:minutes];
	
	// NOTE: I don't know how exactly this calendar deals with negative years, or the transition from Julian
	NSCalendar* gregorian = [[[NSCalendar alloc] initWithCalendarIdentifier:NSGregorianCalendar] autorelease];
	[gregorian setTimeZone:[NSTimeZone timeZoneForSecondsFromGMT:timeZoneSeconds]];
	NSDate* dateWithoutSeconds = [gregorian dateFromComponents:parsedComponents];
	NSDate* date = [dateWithoutSeconds dateByAddingTimeInterval:seconds];
	return date;
}

+ (NSString*)tl_dateToRFC3339:(NSDate*)date withTimezone:(NSTimeZone*)tz {
    NSCalendar* gregorian = [[[NSCalendar alloc] initWithCalendarIdentifier:NSGregorianCalendar] autorelease];
    NSString* tzString;
    
    // this is aligned with RFC3339 distinction among -00:00, +00:00 and Z
    if (tz) {
        [gregorian setTimeZone:tz];
        if ([[tz name] isEqualToString:@"UTC"] || [[tz name] isEqualToString:@"GMT"]) {
            tzString = @"Z";
        } else {
            NSInteger tzSeconds = [tz secondsFromGMTForDate:date];
            double subminutes_offset = abs(tzSeconds) / 60.0;
            NSUInteger hours_offset = floor(subminutes_offset / 60);
            NSUInteger minutes_offset = lround(subminutes_offset - 60 * hours_offset);
            tzString = [NSString stringWithFormat:@"%c%02lu:%02lu", (tzSeconds < 0) ? '-' : '+', hours_offset, minutes_offset];
        }
    } else {
        [gregorian setTimeZone:[NSTimeZone timeZoneForSecondsFromGMT:0]];
        // RFC3339 denotes negative 0 for unknown timezone
        tzString = @"-00:00";
    }
    
    NSDateComponents* d = [gregorian components:TLYMDHMSCalendarUnit fromDate:date];
    double subseconds = [date timeIntervalSinceDate:[gregorian dateFromComponents:d]];
    if (subseconds) {
        return [NSString stringWithFormat:@"%lu-%02lu-%02luT%02lu:%02lu:%02.3f%@", [d year], [d month], [d day], [d hour], [d minute], [d second] + subseconds, tzString];
    } else {
        return [NSString stringWithFormat:@"%lu-%02lu-%02luT%02lu:%02lu:%02lu%@", [d year], [d month], [d day], [d hour], [d minute], [d second], tzString];
    }
}

@end
