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

package org.opensha.commons.param.event;

import java.util.EventListener;

/**
 * <b>Title:</b> ParameterChangeListener
 * <p>
 * 
 * <b>Description:</b> The change listener receives change events whenever one
 * of the Parameters have been edited in the ParameterEditor. The listener is
 * typically the Main Application that wants to do something with the changed
 * data, such as generate a new plot.
 * <p>
 * 
 * @author Steven W. Rock
 * @created February 21, 2002
 * @version 1.0
 */

public interface ParameterChangeListener extends EventListener {
    /**
     * Function that must be implemented by all Listeners for
     * ParameterChangeEvents.
     * 
     * @param event
     *            The Event which triggered this function call
     */
    public void parameterChange(ParameterChangeEvent event);
}
