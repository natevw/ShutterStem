//
//  NSData+TLBase64.h
//  getphoto-osx
//
//  Created by Nathan Vander Wilt on 12/31/10.
//  Copyright 2010 Calf Trail Software, LLC. All rights reserved.
//

#import <Cocoa/Cocoa.h>


@interface NSData (TLBase64)

+ (NSData*)tl_dataByBase64DecodingString:(NSString*)encodedData;
- (NSString*)tl_base64EncodedString;

@end
