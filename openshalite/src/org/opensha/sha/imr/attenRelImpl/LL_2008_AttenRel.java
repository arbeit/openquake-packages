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
import org.opensha.sha.imr.attenRelImpl.constants.LL2008Constants;
import org.opensha.sha.imr.param.EqkRuptureParams.FocalDepthParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceHypoParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <b>Title:</b> LL_2008_AttenRel
 * <p>
 * <b>Description:</b> Class implementing attenuation relationship described
 * in:Ground-Motion Attenuation Relationships for Subduction-Zone Earthquakes in
 * Northeastern Taiwan , Po-Shen Lin and Chyi-Tyi Lee, Bulletin of the
 * Seismological Society of America, Vol. 98, No. 1, pp 220-240, 2008.
 * <p>
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment magnitude
 * <LI>distancehypoParam - hypocentral distance
 * <LI>vs30Param - shear wave velocity (m/s) averaged over the top 30 m of the
 * soil profile; The model assumes the following classification: vs30 > 360 ->
 * ROCK SITES (Class NEHRP B+C); vs30 < 360 -> SOIl SITES (Class NEHRP D+E);
 * <LI>tectonicRegionTypeParam - interface or intra slab
 * <LI>focalDepthParam - depth to the earthquake rupture hypocenter
 * <LI>componentParam - average horizontal
 * <LI>stdDevTypeParam - total, none
 * </UL>
 * <p>
 * 
 * <p>
 * 
 * Verification - This model has been validated (see {@link LL_2008_test}) using
 * tables from Elise Delavaud using mathSHA.
 * </p>
 * 
 ** 
 * @author L. Danciu,
 * @version 1.0, December 2010
 */
public class LL_2008_AttenRel extends AttenuationRelationship implements
		ScalarIntensityMeasureRelationshipAPI,

		NamedObjectAPI, ParameterChangeListener {

	/** Short name. */
	public static final String SHORT_NAME = "LL2008";

	/** Full name. */
	public static final String NAME = "Lin & Lee 2008";

	/** Version number. */
	private static final long serialVersionUID = 1234567828711796187L;

	/** Moment magnitude. */
	private double mag;

	/** Tectonic region type. */
	private String tecRegType;

	/** Focal depth. */
	private double focalDepth;

	/** Vs 30. */
	private double vs30;

	/** Closest distance to rupture. */
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
	public LL_2008_AttenRel(final ParameterChangeWarningListener warningListener) {

		// creates exceedProbParam
		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();

		// init the period hashmap
		indexFromPerHashMap = new HashMap<Double, Integer>();
		for (int i = 1; i < LL2008Constants.PERIOD.length; i++) {
			indexFromPerHashMap.put(new Double(LL2008Constants.PERIOD[i]),
					new Integer(i));
		}

		initEqkRuptureParams();
		initSiteParams();
		initPropagationEffectParams();
		initOtherParams();
		initIndependentParamLists();
		initParameterEventListeners();
	}

	/**
	 * Creates the three supported IM parameters (PGA and SA), as well as the
	 * independenParameters of SA (periodParam and dampingParam) and adds them
	 * to the supportedIMParams list. Makes the parameters non-editable.
	 */
	protected final void initSupportedIntensityMeasureParams() {

		// set supported periods for spectral acceleration
		DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
		for (int i = 1; i < LL2008Constants.PERIOD.length; i++) {
			periodConstraint.addDouble(new Double(LL2008Constants.PERIOD[i]));
		}
		periodConstraint.setNonEditable();
		// set period param (default is 1s, which is provided by LL2008 GMPE)
		saPeriodParam = new PeriodParam(periodConstraint);

		// set damping parameter. Empty constructor set damping
		// factor to 5 % (which is the one provided by LL2008 GMPE)
		saDampingParam = new DampingParam();

		// initialize spectral acceleration parameter (units: g)
		saParam = new SA_Param(saPeriodParam, saDampingParam);
		saParam.setNonEditable();

		// initialize peak ground acceleration parameter (units: g)
		pgaParam = new PGA_Param();
		pgaParam.setNonEditable();

		// add the warning listeners
		saParam.addParameterChangeWarningListener(warningListener);
		pgaParam.addParameterChangeWarningListener(warningListener);

		// put parameters in the supportedIMParams list
		supportedIMParams.clear();
		supportedIMParams.addParameter(saParam);
		supportedIMParams.addParameter(pgaParam);

	}

	/**
	 * Initialize earthquake rupture parameter (moment magnitude, tectonic
	 * region type, focal depth) and add to eqkRuptureParams list. Makes the
	 * parameters non-editable.
	 */
	protected final void initEqkRuptureParams() {

		magParam = new MagParam(LL2008Constants.MAG_WARN_MIN,
				LL2008Constants.MAG_WARN_MAX);

		StringConstraint options = new StringConstraint();
		options.addString(TectonicRegionType.SUBDUCTION_INTERFACE.toString());
		options.addString(TectonicRegionType.SUBDUCTION_SLAB.toString());
		tectonicRegionTypeParam = new TectonicRegionTypeParam(options,
				TectonicRegionType.SUBDUCTION_INTERFACE.toString());

		// default value is 0
		focalDepthParam = new FocalDepthParam();

		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(tectonicRegionTypeParam);
		eqkRuptureParams.addParameter(focalDepthParam);
	}

	/**
	 * Initialize site parameters (vs30) and adds it to the siteParams list.
	 * Makes the parameters non-editable.
	 */
	protected final void initSiteParams() {

		// vs30 parameters (constrains are not set, default value to 760 m/s)
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
				LL2008Constants.DISTANCE_HYPO_WARN_MIN);
		distanceHypoParam.addParameterChangeWarningListener(warningListener);
		DoubleConstraint warn = new DoubleConstraint(new Double(0.0),
				LL2008Constants.DISTANCE_HYPO_WARN_MAX);
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
		meanIndependentParams.addParameter(tectonicRegionTypeParam);
		meanIndependentParams.addParameter(vs30Param);
		meanIndependentParams.addParameter(distanceHypoParam);
		meanIndependentParams.addParameter(focalDepthParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(tectonicRegionTypeParam);
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
	protected final void initParameterEventListeners() {

		// earthquake rupture params
		magParam.addParameterChangeListener(this);
		tectonicRegionTypeParam.addParameterChangeListener(this);
		focalDepthParam.addParameterChangeListener(this);

		// site params
		vs30Param.addParameterChangeListener(this);

		// propagation effect param
		distanceHypoParam.addParameterChangeListener(this);

		// standard deviation type param
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
		} else if (pName.equals(TectonicRegionTypeParam.NAME)) {
			tecRegType = (String) val;
		} else if (pName.equals(FocalDepthParam.NAME)) {
			focalDepth = ((Double) val).doubleValue();
		} else if (pName.equals(Vs30_Param.NAME)) {
			vs30 = ((Double) val).doubleValue();
		} else if (pName.equals(DistanceHypoParameter.NAME)) {
			rhypo = ((Double) val).doubleValue();
		} else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = (String) val;
		}
	}

	/**
	 * Allows to reset the change listeners on the parameters.
	 */
	public final void resetParameterEventListeners() {
		magParam.removeParameterChangeListener(this);
		tectonicRegionTypeParam.removeParameterChangeListener(this);
		focalDepthParam.removeParameterChangeListener(this);
		vs30Param.removeParameterChangeListener(this);
		distanceHypoParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}

	/**
	 * This sets the eqkRupture related parameters (moment magnitude, tectonic
	 * region type, focal depth) based on the eqkRupture passed in. The
	 * internally held eqkRupture object is also set as that passed in. Warning
	 * constrains on magnitude and focal depth are ignored.
	 */
	public final void setEqkRupture(final EqkRupture eqkRupture) {

		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

		if (eqkRupture.getTectRegType() != null) {
			tectonicRegionTypeParam.setValue(eqkRupture.getTectRegType()
					.toString());
		} else {
			throw new RuntimeException("Tectonic region type not set in "
					+ " earthquake rupture");
		}
		
		if (eqkRupture.getHypocenterLocation() != null) {
			focalDepthParam.setValue(eqkRupture.getHypocenterLocation().getDepth());
		} else {
			throw new RuntimeException("Hypocenter not set in "
					+ " earthquake rupture");
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
	 * This sets the site and eqkRupture, and the related parameters, from the
	 * propEffect object passed in.
	 */

	public final void setPropagationEffectParams() {
		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceHypoParam.setValue(eqkRupture, site);
		}
	}

	/**
	 * Set period index.
	 */
	protected final void setPeriodIndex() {
		if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
			iper = 0;
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
			return getMean(iper, mag, rhypo, focalDepth, vs30, tecRegType);
		}
	}

	/**
	 * Compute standard deviation.
	 */
	public final double getStdDev() {

		setPeriodIndex();

		return getStdDev(iper, stdDevType, vs30);
	}

	/**
	 * Allows the user to set the default parameter values for the selected
	 * Attenuation Relationship.
	 */
	public final void setParamDefaults() {

		magParam.setValueAsDefault();
		tectonicRegionTypeParam.setValueAsDefault();
		focalDepthParam.setValueAsDefault();
		vs30Param.setValueAsDefault();
		distanceHypoParam.setValueAsDefault();
		saPeriodParam.setValueAsDefault();
		saDampingParam.setValueAsDefault();
		saParam.setValueAsDefault();
		pgaParam.setValueAsDefault();
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
	 * Compute mean (natural logarithm of median ground motion).
	 */

	public double getMean(int iper, double mag, double rhypo, double hypoDepth,
			final double vs30, final String tecRegType) {

		double Zt;
		double logY;

		if (tecRegType.equals(TectonicRegionType.SUBDUCTION_INTERFACE
				.toString())) {
			Zt = 0;
		} else {
			Zt = 1;
		}

		if (vs30 >= LL2008Constants.SOIL_TYPE_SOFT_UPPER_BOUND) {
			double term1 = LL2008Constants.rock_C2[iper] * mag;
			double r = rhypo + LL2008Constants.rock_C4[iper]
					* Math.exp(LL2008Constants.rock_C5[iper] * mag);
			double term2 = LL2008Constants.rock_C3[iper] * Math.log(r);
			double term3 = LL2008Constants.rock_C6[iper] * hypoDepth;
			logY = LL2008Constants.rock_C1[iper] + term1 + term2 + term3
					+ LL2008Constants.rock_C7[iper] * Zt;
		} else {
			double term1 = LL2008Constants.soil_C2[iper] * mag;
			double r = rhypo + LL2008Constants.soil_C4[iper]
					* Math.exp(LL2008Constants.soil_C5[iper] * mag);
			double term2 = LL2008Constants.soil_C3[iper] * Math.log(r);
			double term3 = LL2008Constants.soil_C6[iper] * hypoDepth;
			logY = LL2008Constants.soil_C1[iper] + term1 + term2 + term3
					+ LL2008Constants.soil_C7[iper] * Zt;
		}

		return logY;
	}

	/**
	 * @return The stdDev value
	 */
	public double getStdDev(int iper, String stdDevType, double vs30) {
		double sigmaR, sigmaS;
		if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) {
			return 0.0;
		} else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) {
			if (vs30 >= LL2008Constants.SOIL_TYPE_SOFT_UPPER_BOUND) {
				sigmaR = LL2008Constants.ROCK_TOTAL_STD[iper];
				return (sigmaR);
			} else {
				sigmaS = LL2008Constants.soil_TOTAL_STD[iper];
				return (sigmaS);
			}
		} else {
			throw new RuntimeException("Standard deviation type: "+stdDevType+" not recognized");
		}
	}

	/**
	 * This provides a URL where more info on this model can be obtained return
	 * null because no URL has been created.
	 */
	public URL getInfoURL() throws MalformedURLException {
		return null;
	}
}
