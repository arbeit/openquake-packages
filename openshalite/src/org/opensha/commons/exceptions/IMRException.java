/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.exceptions;

/**
 * <b>Title:</b> IMRException
 * <p>
 * 
 * <b>Description:</b> Exception thrown when constraints reject setting a
 * Parameter value inside the IMR GUI Tester
 * <p>
 * 
 * Note: These exception subclasses add no new functionality. It's really the
 * class name that is the important information. The name indicates what type of
 * error it is and helps to pinpoint where the error could have occured in the
 * code. It it much easier to see different exception types than have one
 * catchall RuntimeException type.
 * <p>
 * 
 * @author Steven W. Rock
 * @created February 20, 2002
 * @version 1.0
 */

public final class IMRException extends RuntimeException {

    /** No-arg constructor */
    public IMRException() {
        super();
    }

    /** Constructor that specifies an error message */
    public IMRException(String string) {
        super(string);
    }
}
