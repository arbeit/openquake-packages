/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.constants.CF2008Constants;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RakeParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceHypoParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> CF_2008_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the GMPE published by Cauzzi & Faccioli
 * (2008, Broadband (0.05 to 20s) prediction of displacement response spectra
 * based on worldwide digital records , journal of Seismology, Volume 12,pp.
 * 453-475) This implements only horizontal components and the equation (2) page
 * 462.
 * 
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>pgvParam - Peak Ground Velocity (added according to personal communication)
 * <LI>saParam = ((2*pi/T)^2)*sdParam Convert to Acceleration Response Spectra
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceHypo - hypocentral(focal) distance;
 * <LI>vs30Param [>= 800m/sec] default 30-meter shear wave velocity; The model
 * assumes the following classification (based on EC 8 scheme): vs30 >= 800 ->
 * Class A (rock-like); 360 <= vs30 <800 -> Class B (Stiff Soil); 180 <= vs30 <
 * 360 -> Class C (Soft Soil); vs30 < 180 -> Class D (Very Soft Soil);
 * <LI>fltTypeParam - Style of faulting
 * <LI>componentParam - [geometric mean] default component of shaking
 * <LI>stdDevTypeParam - total and none
 * </UL>
 * </p>
 * 
 * <p>
 * 
 * Verification - This model has been tested (see {@link CF_2008_test} using
 * tables from original authors)
 * 
 * </p>
 * 
 * 
 * @author L. Danciu
 * @created August, 2010
 * @version 1.0
 */

public class CF_2008_AttenRel extends AttenuationRelationship implements
		ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
		ParameterChangeListener {

	/** Short name. */
	public static final String SHORT_NAME = "CF2008";

	/** Full name. */
	public static final String NAME = "Cauzzi & Faccioli (2008)";

	/** Version number. */
	private static final long serialVersionUID = 1234567890987654353L;

	/** Moment magnitude. */
	private double mag;

	/** rake angle. */
	private double rake;

	/** Vs 30. */
	private double vs30;

	/** hypocentral distance */
	private double rhypo;

	/** Standard deviation type. */
	private String stdDevType;

	/** Map period-value/period-index. */
	private HashMap<Double, Integer> indexFromPerHashMap;

	/** Period index. */
	private int iper;

	/** For issuing warnings. */
	private transient ParameterChangeWarningListener warningListener = null;

	/**
	 * Construct attenuation relationship. Initialize parameters and parameter
	 * lists.
	 */
	public CF_2008_AttenRel(ParameterChangeWarningListener warningListener) {

		// creates exceedProbParam
		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();

		indexFromPerHashMap = new HashMap<Double, Integer>();
		for (int i = 2; i < CF2008Constants.PERIOD.length; i++) {
			indexFromPerHashMap.put(new Double(CF2008Constants.PERIOD[i]),
					new Integer(i));
		}

		// Initialize earthquake Rupture parameters (e.g. magnitude)
		initEqkRuptureParams();
		// Initialize Propagation Effect Parameters (e.g. source-site distance)
		initPropagationEffectParams();
		// Initialize site parameters (e.g. vs30)
		initSiteParams();
		// Initialize other parameters (e.g. stress drop)
		initOtherParams();
		// Initialize the independent parameters list
		initIndependentParamLists();
		// Initialize the parameter change listeners
		initParameterEventListeners();
	}

	/**
	 * Creates the two supported IM parameters (PGA and SA), as well as the
	 * independenParameters of SA (periodParam and dampingParam) and adds them
	 * to the supportedIMParams list. Makes the parameters non-editable.
	 */
	protected final void initSupportedIntensityMeasureParams() {

		// set supported periods for spectral acceleration
		DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
		for (int i = 2; i < CF2008Constants.PERIOD.length; i++) {
			periodConstraint.addDouble(new Double(CF2008Constants.PERIOD[i]));
		}
		periodConstraint.setNonEditable();
		// set period param (default is 1s, which is provided by CF2008 GMPE)
		saPeriodParam = new PeriodParam(periodConstraint);

		// set damping parameter. Empty constructor set damping
		// factor to 5 % (which is the one provided by CF2008 GMPE)
		saDampingParam = new DampingParam();

		// initialize spectral acceleration parameter (units: g)
		saParam = new SA_Param(saPeriodParam, saDampingParam);
		saParam.setNonEditable();

		// initialize peak ground acceleration parameter (units: g)
		pgaParam = new PGA_Param();
		pgaParam.setNonEditable();

		// initialize peak ground velocity parameter (units: cm/sec)
		pgvParam = new PGV_Param();
		pgvParam.setNonEditable();

		// add the warning listeners
		saParam.addParameterChangeWarningListener(warningListener);
		pgaParam.addParameterChangeWarningListener(warningListener);
		pgvParam.addParameterChangeWarningListener(warningListener);

		// put parameters in the supportedIMParams list
		supportedIMParams.clear();
		supportedIMParams.addParameter(saParam);
		supportedIMParams.addParameter(pgaParam);
		supportedIMParams.addParameter(pgvParam);

	}

	/**
	 * Initialize earthquake rupture parameter (moment magnitude, rake) and add
	 * to eqkRuptureParams list. Makes the parameters non-editable.
	 */
	protected final void initEqkRuptureParams() {

		// moment magnitude (default 5.0)
		magParam = new MagParam(CF2008Constants.MAG_WARN_MIN,
				CF2008Constants.MAG_WARN_MAX);
		// Focal mechanism
		rakeParam = new RakeParam();
		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(rakeParam);

	}

	/**
	 * Initialize the site type geology from the Vs30 value.
	 * 
	 * @param vs30
	 *            default 30-meter shear wave velocity
	 */
	protected final void initSiteParams() {

		vs30Param = new Vs30_Param();

		siteParams.clear();
		siteParams.addParameter(vs30Param);
	}

	/**
	 * Initialize Propagation Effect parameters (closest distance to rupture)
	 * and adds them to the propagationEffectParams list. Makes the parameters
	 * non-editable.
	 */
	protected final void initPropagationEffectParams() {

		distanceHypoParam = new DistanceHypoParameter(
				CF2008Constants.DISTANCE_HYPO_WARN_MIN);
		distanceHypoParam.addParameterChangeWarningListener(warningListener);
		DoubleConstraint warn = new DoubleConstraint(new Double(0.00),
				CF2008Constants.DISTANCE_HYPO_WARN_MAX);
		warn.setNonEditable();
		distanceHypoParam.setWarningConstraint(warn);
		distanceHypoParam.setNonEditable();

		propagationEffectParams.addParameter(distanceHypoParam);
	}

	/**
	 * Initialize other Parameters (standard deviation type, component, sigma
	 * truncation type, sigma truncation level).
	 */
	protected final void initOtherParams() {

		sigmaTruncTypeParam = new SigmaTruncTypeParam();
		sigmaTruncLevelParam = new SigmaTruncLevelParam();

		// stdDevType Parameter
		StringConstraint stdDevTypeConstraint = new StringConstraint();
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
		stdDevTypeConstraint.setNonEditable();
		stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

		// component Parameter
		StringConstraint constraint = new StringConstraint();
		constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
		constraint.setNonEditable();
		componentParam = new ComponentParam(constraint,
				ComponentParam.COMPONENT_AVE_HORZ);

		// add these to the list
		otherParams.clear();
		otherParams.addParameter(sigmaTruncTypeParam);
		otherParams.addParameter(sigmaTruncLevelParam);
		otherParams.addParameter(stdDevTypeParam);
		otherParams.addParameter(componentParam);
	}

	/**
	 * This creates the lists of independent parameters that the various
	 * dependent parameters (mean, standard deviation, exceedance probability,
	 * and IML at exceedance probability) depend upon. NOTE: these lists do not
	 * include anything about the intensity-measure parameters or any of their
	 * internal independentParamaters.
	 */
	protected final void initIndependentParamLists() {

		// params that the mean depends upon
		meanIndependentParams.clear();
		meanIndependentParams.addParameter(magParam);
		meanIndependentParams.addParameter(vs30Param);
		meanIndependentParams.addParameter(distanceHypoParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(stdDevTypeParam);

		// params that the exceed. prob. depends upon
		exceedProbIndependentParams.clear();
		exceedProbIndependentParams.addParameterList(meanIndependentParams);
		exceedProbIndependentParams.addParameter(stdDevTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

		// params that the IML at exceed. prob. depends upon
		imlAtExceedProbIndependentParams
				.addParameterList(exceedProbIndependentParams);
		imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
	}

	/**
	 * Adds the parameter change listeners. This allows to listen to when-ever
	 * the parameter is changed.
	 */
	protected void initParameterEventListeners() {

		magParam.addParameterChangeListener(this);
		rakeParam.addParameterChangeListener(this);
		vs30Param.addParameterChangeListener(this);
		distanceHypoParam.addParameterChangeListener(this);
		stdDevTypeParam.addParameterChangeListener(this);
	}

	/**
	 * This listens for parameter changes and updates the primitive parameters
	 * accordingly
	 */
	public final void parameterChange(final ParameterChangeEvent e) {

		String pName = e.getParameterName();
		Object val = e.getNewValue();

		if (pName.equals(MagParam.NAME)) {
			mag = ((Double) val).doubleValue();
		} else if (pName.equals(Vs30_Param.NAME)) {
			vs30 = ((Double) val).doubleValue();
		} else if (pName.equals(DistanceHypoParameter.NAME)) {
			rhypo = ((Double) val).doubleValue();
		} else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = (String) val;
		} else if (pName.equals(FaultTypeParam.NAME)) {
			rake = ((Double) val).doubleValue();
		}
	}

	/**
	 * Allows to reset the change listeners on the parameters
	 */
	public void resetParameterEventListeners() {
		magParam.removeParameterChangeListener(this);
		rakeParam.removeParameterChangeListener(this);
		vs30Param.removeParameterChangeListener(this);
		distanceHypoParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}

	/**
	 * This sets the eqkRupture related parameters (moment magnitude, rake)
	 * based on the eqkRupture passed in. The internally held eqkRupture object
	 * is also set.
	 */
	public final void setEqkRupture(final EqkRupture eqkRupture) {

		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
		if (!Double.isNaN(eqkRupture.getAveRake())) {
			rakeParam.setValue(eqkRupture.getAveRake());
		}
		this.eqkRupture = eqkRupture;
		setPropagationEffectParams();
	}

	/**
	 * This sets the site-related parameter (vs30) based on what is in the Site
	 * object passed in. This also sets the internally held Site object as that
	 * passed in.
	 */
	public final void setSite(final Site site) {
		vs30Param.setValueIgnoreWarning((Double) site.getParameter(
				Vs30_Param.NAME).getValue());
		this.site = site;
		setPropagationEffectParams();
	}

	/**
	 * This calculates the Hypocentral Distance propagation effect parameter
	 * based on the current site and eqkRupture.
	 * <P>
	 */
	protected void setPropagationEffectParams() {

		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceHypoParam.setValue(this.eqkRupture, this.site);
		}
	}

	/**
	 * Set period index.
	 */
	protected final void setPeriodIndex() {
		if (im.getName().equalsIgnoreCase(PGV_Param.NAME)) {
			iper = 0;
		} else if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
			iper = 1;
		} else {
			iper = ((Integer) indexFromPerHashMap.get(saPeriodParam.getValue()))
					.intValue();
		}
	}

	/**
	 * Compute mean.
	 */
	public double getMean() {
		if (rhypo > USER_MAX_DISTANCE) {
			return VERY_SMALL_MEAN;
		} else {
			setPeriodIndex();
			return getMean(iper, mag, rhypo, vs30, rake);
		}
	}

	/**
	 * Compute standard deviation.
	 */
	public final double getStdDev() {

		setPeriodIndex();
		return getStdDev(iper, stdDevType);
	}

	/**
	 * Allows the user to set the default parameter values for the selected
	 * Attenuation Relationship.
	 */
	public final void setParamDefaults() {

		magParam.setValueAsDefault();
		rakeParam.setValueAsDefault();
		vs30Param.setValueAsDefault();
		distanceHypoParam.setValueAsDefault();
		saPeriodParam.setValueAsDefault();
		saDampingParam.setValueAsDefault();
		saParam.setValueAsDefault();
		pgaParam.setValueAsDefault();
		pgvParam.setValueAsDefault();
		stdDevTypeParam.setValueAsDefault();
		sigmaTruncTypeParam.setValueAsDefault();
		sigmaTruncLevelParam.setValueAsDefault();
		componentParam.setValueAsDefault();
	}

	/**
	 * Get the name of this IMR.
	 */
	public final String getName() {
		return NAME;
	}

	/**
	 * Returns the Short Name of each AttenuationRelationship
	 * 
	 */
	public final String getShortName() {
		return SHORT_NAME;
	}

	/**
	 * This computes the mean log10(Y)
	 * 
	 * @param iper
	 * @param rhypo
	 * @param mag
	 */
	public double getMean(int iper, double mag, double rhypo,
			final double vs30, final double rake) {

		double logY;

		// This is to avoid rhypo == 0 distances
		if (rhypo < CF2008Constants.DISTANCE_HYPO_WARN_MIN) {
			rhypo = CF2008Constants.DISTANCE_HYPO_WARN_MIN;
		}

		double[] s = computeSiteTerm(iper, vs30);
		double[] f = computeStyleOfFaultingTerm(iper, rake);

		double term1 = CF2008Constants.a1[iper] + CF2008Constants.a2[iper]
				* mag;

		double term2 = CF2008Constants.a3[iper] * Math.log10(rhypo);

		logY = term1 + term2 + s[2] + f[2];

		logY *= CF2008Constants.LOG10_2_LN;

		// tmp variable to convert to DRS to mean PSA(g);
		double tmp1 = Math.pow((2 * Math.PI) / CF2008Constants.PERIOD[iper], 2);

		if (iper == 0) {
			logY = Math.exp(logY);
		} else if (iper == 1) {
			logY = Math.exp(logY) * CF2008Constants.MSS_TO_G_CONVERSION_FACTOR;
		} else {
			logY = Math.exp(logY) * tmp1
					* CF2008Constants.CMS_TO_G_CONVERSION_FACTOR;
		}
		return Math.log(logY);
	}

	private double[] computeSiteTerm(final int iper, final double vs30) {
		double[] s = new double[3];
		if (vs30 > CF2008Constants.SOIL_TYPE_ROCK_UPPER_BOUND) {
			s[0] = 0.0;
			s[1] = 0.0;
			s[2] = 0.0;
		} else if (vs30 >= CF2008Constants.SITE_TYPE_STIFF_SOIL_UPPER_BOUND
				&& vs30 < CF2008Constants.SOIL_TYPE_ROCK_UPPER_BOUND) {
			s[0] = 1.00;
			s[1] = 0.00;
			s[2] = s[0] * CF2008Constants.aB[iper];
		} else if (vs30 >= CF2008Constants.SITE_TYPE_SOFT_UPPER_BOUND
				&& vs30 < CF2008Constants.SITE_TYPE_STIFF_SOIL_UPPER_BOUND) {
			s[0] = 0.00;
			s[1] = 1.00;
			s[2] = s[1] * CF2008Constants.aC[iper];
		} else if (vs30 < CF2008Constants.SITE_TYPE_SOFT_UPPER_BOUND) {
			s[0] = 0.00;
			s[1] = 0.00;
			s[2] = CF2008Constants.aD[iper];
		}
		return s;
	}

	// set fault mechanism
	private double[] computeStyleOfFaultingTerm(final int iper,
			final double rake) {
		double[] f = new double[3];
		if (rake > CF2008Constants.FLT_TYPE_NORMAL_RAKE_LOWER
				&& rake <= CF2008Constants.FLT_TYPE_NORMAL_RAKE_UPPER) {
			f[0] = 1.00;
			f[1] = 0.00;
			f[2] = f[0] * CF2008Constants.aN[iper];
		} else if (rake > CF2008Constants.FLT_TYPE_REVERSE_RAKE_LOWER
				&& rake <= CF2008Constants.FLT_TYPE_REVERSE_RAKE_UPPER) {
			f[0] = 0.00;
			f[1] = 1.00;
			f[2] = f[1] * CF2008Constants.aR[iper];
		} else {
			f[0] = 0.00;
			f[1] = 0.00;
			f[2] = CF2008Constants.aS[iper];
		}
		return f;
	}

	public double getStdDev(int iper, String stdDevType) {
		if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			return 0;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			return CF2008Constants.LOG10_2_LN * CF2008Constants.TOTAL_STD[iper];
		else
			throw new RuntimeException("Standard deviation type: "+stdDevType+" not recognized");
	}

	/**
	 * This provides a URL where more info on this model can be obtained. It
	 * currently returns null because no URL has been set up.
	 */
	public final URL getInfoURL() throws MalformedURLException {
		return null;
	}
}
