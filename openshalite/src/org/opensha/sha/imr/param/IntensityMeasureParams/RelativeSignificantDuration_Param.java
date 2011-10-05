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

package org.opensha.sha.imr.param.IntensityMeasureParams;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.WarningDoubleParameter;

/**
 * This constitutes the natural-log relative significant duration intensity measure
 * parameter. See constructors for info on editability and default values.
 * 
 * @author J. Douglas
 * 
 */
public class RelativeSignificantDuration_Param extends WarningDoubleParameter {

	public final static String NAME = "RSD";
	public final static String UNITS = "s";
	public final static String INFO = "Relative significant duration (5-95% of Arias intensity)";
	public final static Double MIN = new Double(Math.log(Double.MIN_VALUE));
	public final static Double MAX = new Double(Double.MAX_VALUE);
	public final static Double DEFAULT_WARN_MIN = new Double(
			Math.log(Double.MIN_VALUE));
	public final static Double DEFAULT_WARN_MAX = new Double(Math.log(2.5));

	/**
	 * This uses the supplied warning constraint and default (both in
	 * natural-log space). The parameter is left as non editable
	 * 
	 * @param warningConstraint
	 * @param defaultRSD
	 */
	public RelativeSignificantDuration_Param(DoubleConstraint warningConstraint, double defaultRSD) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
		this.setInfo(INFO);
		setWarningConstraint(warningConstraint);
		setDefaultValue(defaultRSD);
		setNonEditable();
	}

	/**
	 * This uses the DEFAULT_WARN_MIN and DEFAULT_WARN_MAX fields to set the
	 * warning constraint, and sets the default as Math.log(1.0) (the natural
	 * log of 1.0). The parameter is left as non editable
	 */
	public RelativeSignificantDuration_Param() {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
		setInfo(INFO);
		DoubleConstraint warn2 =
				new DoubleConstraint(DEFAULT_WARN_MIN, DEFAULT_WARN_MAX);
		warn2.setNonEditable();
		setWarningConstraint(warn2);
		setDefaultValue(Math.log(1.0));
		setNonEditable();
	}
}
