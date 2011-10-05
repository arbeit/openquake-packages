package org.opensha.sha.imr.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.constants.FS2011Constants;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RakeParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.IA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> FS_2011_AttenRel
 * <p>
 * 
 * <b>Description:</b> Class implementing attenuation relationship described in:
 * "A predictive model for Arias intensity at multiple sites and consideration 
 * of spatial correlations",
 * Foulser-Piggott, R. & Stafford, P. J. 
 * Earthquake Engineering & Structural Dynamics, 
 * doi: 10.1002/eqe.1137, 2011. in press
 * 
 * <p>
 * 
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>IA_Param - Arias intensity (m/s)
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment magnitude
 * <LI>rakeParam - rake angle. Used to establish if event is reverse/reverse oblique 
 * (22.5 < rake < 112.5) or other mechanism (strike-slip or normal).
 * <LI>distanceRupParam - rupture distance
 * <LI>vs30Param - shear wave velocity (m/s) averaged over the top 30 m of the
 * soil profile; The model uses a continuous site amplification model
 * <LI>componentParam - geometric mean horizontal
 * <LI>stdDevTypeParam - total, inter-event, intra-event, none
 * </UL>
 * <p>
 * 
 * <p>
 * 
 * Verification -
 * Checked against my previous Fortran implementation of this GMPE
 * and against results of StaffordGMPEs.jar provided by Peter J.
 * Stafford
 * 
 * 
 * </p>
 * 
 ** 
 * @author J. Douglas
 * @created August 31, 2011
 * @version 1.1
 */

public class FS_2011_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
ParameterChangeListener {

	/** Short name. */
	public final static String SHORT_NAME = "FS2011";

	/** Full name. */
	public final static String NAME = "Foulser-Piggott & Stafford (2011)";

	/** Version number. */
	private static final long serialVersionUID = 1234567890987654353L;

	/** Moment magnitude. */
	private double mag;

	/** rake angle. */
	private double rake;

	/** Rupture distance. */
	private double rrup;

	/** Vs30. */
	private double vs30;

	/** Standard deviation type. */
	private String stdDevType;

	/** For issuing warnings. */
	private transient ParameterChangeWarningListener warningListener = null;

	/**
	 * Construct attenuation relationship. Initialize parameters and parameter
	 * lists.
	 */
	public FS_2011_AttenRel(
			final ParameterChangeWarningListener warningListener) {

		// creates exceedProbParam
		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();

		initEqkRuptureParams();
		initPropagationEffectParams();
		initSiteParams();
		initOtherParams();
		initIndependentParamLists();
		initParameterEventListeners();
	}

	/**
	 * Creates the supported IM parameter (IA) and adds
	 * them to the supportedIMParams list. Makes the parameters non-editable.
	 */
	protected final void initSupportedIntensityMeasureParams() {

		// initialize Arias intensity (units: m/s)
		aiParam = new IA_Param();
		aiParam.setNonEditable();

		// add the warning listeners
		aiParam.addParameterChangeWarningListener(warningListener);

		// put parameters in the supportedIMParams list
		supportedIMParams.clear();
		supportedIMParams.addParameter(aiParam);
	}

	/**
	 * Initialize earthquake rupture parameter (moment magnitude, rake) and add
	 * to eqkRuptureParams list. Makes the parameters non-editable.
	 */
	protected final void initEqkRuptureParams() {

		// moment magnitude (default 5.5)
		magParam = new MagParam(FS2011Constants.MAG_WARN_MIN,
				FS2011Constants.MAG_WARN_MAX);
		// rake angle (default 0.0 -> strike-slip)
		rakeParam = new RakeParam();

		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(rakeParam);
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
	 * Initialize Propagation Effect parameters (rupture distance) and adds
	 * them to the propagationEffectParams list. Makes the parameters
	 * non-editable.
	 */
	protected final void initPropagationEffectParams() {

		distanceRupParam = new DistanceRupParameter(
				FS2011Constants.DISTANCE_RUP_WARN_MIN);
		distanceRupParam.addParameterChangeWarningListener(warningListener);
		DoubleConstraint warn = new DoubleConstraint(
				FS2011Constants.DISTANCE_RUP_WARN_MIN,
				FS2011Constants.DISTANCE_RUP_WARN_MAX);
		warn.setNonEditable();
		distanceRupParam.setWarningConstraint(warn);
		distanceRupParam.setNonEditable();

		propagationEffectParams.addParameter(distanceRupParam);
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
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
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
		meanIndependentParams.addParameter(rakeParam);
		meanIndependentParams.addParameter(distanceRupParam);
		meanIndependentParams.addParameter(vs30Param);

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
		distanceRupParam.addParameterChangeListener(this);
		vs30Param.addParameterChangeListener(this);
		componentParam.addParameterChangeListener(this);
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
		} else if (pName.equals(RakeParam.NAME)) {
			rake = ((Double) val).doubleValue();
		} else if (pName.equals(DistanceRupParameter.NAME)) {
			rrup = ((Double) val).doubleValue();
		} else if (pName.equals(Vs30_Param.NAME)) {
			vs30 = ((Double) val).doubleValue();
		} else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = (String) val;
		}
	}

	/**
	 * Allows to reset the change listeners on the parameters
	 */
	public void resetParameterEventListeners() {

		magParam.removeParameterChangeListener(this);
		rakeParam.removeParameterChangeListener(this);
		distanceRupParam.removeParameterChangeListener(this);
		vs30Param.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}

	/**
	 * This sets the eqkRupture related parameters (moment magnitude, rake
	 * angle) based on the eqkRupture passed in. The internally held eqkRupture
	 * object is also set as that passed in.
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
	 * This calculates the rupture distance propagation effect parameter based on the
	 * current site and eqkRupture.
	 */
	protected void setPropagationEffectParams() {

		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceRupParam.setValue(eqkRupture, site);
		}
	}

	/**
	 * Compute mean.
	 */
	public double getMean() {

		if (rrup > USER_MAX_DISTANCE) {
			return VERY_SMALL_MEAN;
		} else {
			return getMean(mag, rrup, vs30, rake);
		}
	}

	/**
	 * Compute standard deviation.
	 */
	public final double getStdDev() {

		return getStdDev(mag,rrup,vs30,rake,stdDevType);
	}

	/**
	 * Allows the user to set the default parameter values for the selected
	 * Attenuation Relationship.
	 */
	public final void setParamDefaults() {

		magParam.setValueAsDefault();
		rakeParam.setValueAsDefault();
		distanceRupParam.setValueAsDefault();
		vs30Param.setValueAsDefault();
		aiParam.setValueAsDefault();
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
	public double getMean( double mag, final double rrup,
			final double vs30, final double rake) {

		double lnY = Double.NaN;

		double c1=4.9862;	
		double c2=-0.1939;
		double c3=-4.0332;
		double c4=0.2887;
		double c5=6.3049;
		double c6=0.3507;
		double v1=-1.1576;
		double v2=-0.4576;
		double v3=-0.0029; 
		double v4=0.0818;
		double vref=1100.0;
		double vel1=280.0;

		int faultStyleTerms = setFaultStyleTerms(rake);

		double iaref=Math.exp(c1+c2*(8.5-mag)*(8.5-mag)+(c3+c4*mag)*Math.log(Math.sqrt(rrup*rrup+c5*c5))+c6*faultStyleTerms);
		double fsite=v1*Math.log(vs30/vref)+v2*(Math.exp(v3*(Math.min(vs30, 1100.)-vel1))-Math.exp(v3*(vref-vel1)))*Math.log((iaref+v4)/v4);
		lnY = Math.log(iaref)+fsite;

		return lnY;
	}

	private int setFaultStyleTerms(final double rake) {
		int faultStyleTerms = 0;
		boolean reverse = rake > 22.5 && rake < 112.5;
		if (reverse) {
			faultStyleTerms = 1;
		}
		return faultStyleTerms;
	}

	public double getStdDev(double mag, final double rrup,
			final double vs30,  final double rake, String stdDevType) {
		/**
		 * inter-event
		 */
		double sigmae=0.6556;

		/** 
		 * intra-event
		 */
		double c1=4.9862;	
		double c2=-0.1939;
		double c3=-4.0332;
		double c4=0.2887;
		double c5=6.3049;
		double c6=0.3507;
		double delta1=-0.5921;
		double delta2=3.8311;
		double delta3=4.0762;	
		double v2=-0.4576;
		double v3=-0.0029; 
		double v4=0.0818;
		double vref=1100.0;
		double vel1=280.0;
		double sigmaa=0.5978;

		int faultStyleTerms = setFaultStyleTerms(rake);
		double iaref=Math.exp(c1+c2*(8.5-mag)*(8.5-mag)+(c3+c4*mag)*Math.log(Math.sqrt(rrup*rrup+c5*c5))+c6*faultStyleTerms);
		double b=v2*(Math.exp(v3*(Math.min(vs30, 1100.)-vel1))-Math.exp(v3*(vref-vel1)));
		double c=v4;
		double nl=b*iaref/(iaref+c);
		double sigma=sigmaa*Math.pow(Math.max(mag, 5.), delta1)*(delta2+Math.pow(Math.abs(1+nl),delta3));

		if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
			return 0;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
			return sigmae;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
			return sigma;
		else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
			return Math.sqrt(sigmae*sigmae+sigma*sigma);
		else
			throw new RuntimeException("Standard devition type: "+stdDevType+" not recognized");
	}

	/**
	 * This provides a URL where more info on this model can be obtained.
	 * Currently returns null because no URL has been created
	 */
	public URL getInfoURL() throws MalformedURLException {
		return null;
	}
}
