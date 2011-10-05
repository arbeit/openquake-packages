package org.opensha.sha.imr.attenRelImpl;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.constants.ZhaoEtAl2006Constants;
import org.opensha.sha.imr.param.EqkRuptureParams.FocalDepthParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RakeParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <b>Title:</b> ZhaoEtAl_2006_AttenRel
 * <p>
 * <b>Description:</b> Class implementing attenuation relationship described in:
 * "Attenuation Relations of Strong Ground Motion in Japan Using Site
 * Classification Based on Predominant Period", John X. Zhao et al, Bulletin of
 * the Seismological Society of America, Vol. 96, No. 3, pp 898-913, 2006.
 * <p>
 * Supported Intensity-Measure Parameters:
 * <p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration (5 % damping)
 * </UL>
 * <p>
 * Other Independent Parameters:
 * <p>
 * <UL>
 * <LI>magParam - moment magnitude
 * <LI>distanceRupParam - closest distance to rupture surface
 * <LI>vs30Param - shear wave velocity (m/s) averaged over the top 30 m of the
 * soil profile; The model assumes the following classification: vs30 > 1100 ->
 * Hard Rock, NEHRP A; 600 < vs30 <=1000 -> Rock, NEHRP A+B; 300 < vs30 <= 600
 * -> Hard Soil, NEHRP C; 200 < vs30 <= 300 -> Medium Soil, NEHRP D, vs30 <=200
 * -> Soft Soil, NEHRP E + F;
 * <LI>tectonicRegionTypeParam - shallow crust, interface, intra slab
 * <LI>rakeParam - rake angle. Used to establish reverse faulting for shallow
 * crust events (30 < rake < 150 -> reverse)
 * <LI>focalDepthParam - depth to the earthquake rupture hypocenter
 * <LI>componentParam - geometric mean of two horizontal components, GMRoti50
 * (original model assumes only average horizontal, GMRorti50 added assuming
 * equivalence to average horizontal according to SHARE Report D4.2: Adjustment
 * of GMPEs, S. Drouet, F. Cotton, C. Beauval)
 * <LI>stdDevTypeParam - total, inter-event, intra-event, none
 * </UL>
 * <p>
 * 
 * <p>
 * 
 * Verification - This model has been validated (see {@link ZhaoEtAl_2006_test})
 * against tables computed using the original Zhao's code. Tests were
 * implemented to check median PGA and SA (at different peridos) for shallow
 * crust, interface, intraslab events, at different magnitude (5.0 and 6.5), and
 * different soil conditions.
 * 
 * 
 * </p>
 * 
 ** 
 * @author L.Danciu, Marco Pagani, D. Monelli
 * @version 1.0, December 2010
 */
public class ZhaoEtAl_2006_AttenRel extends AttenuationRelationship implements
		ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
		ParameterChangeListener {

	/** Short name. */
	public static final String SHORT_NAME = "ZhaoEtAl2006";

	/** Full name. */
	public static final String NAME = "Zhao et. al. 2006";

	/** Version number. */
	private static final long serialVersionUID = 1234567890987654353L;

	/** Moment magnitude (Mw) */
	private double mag;

	/** Tectonic region type */
	private String tecRegType;

	/** Focal depth. */
	private double focalDepth;

	/** Vs30. */
	private double vs30;

	/** Closest distance to rupture. */
	private double rRup;

	/** Rake angle. */
	private double rake;

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
	public ZhaoEtAl_2006_AttenRel(ParameterChangeWarningListener warningListener) {

		// creates exceedProbParam
		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();

		indexFromPerHashMap = new HashMap<Double, Integer>();
		for (int i = 0; i < ZhaoEtAl2006Constants.PERIOD.length; i++) {
			indexFromPerHashMap
					.put(new Double(ZhaoEtAl2006Constants.PERIOD[i]),
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
	 * Creates the two supported IM parameters (PGA and SA), as well as the
	 * independenParameters of SA (periodParam and dampingParam) and adds them
	 * to the supportedIMParams list. Makes the parameters non-editable.
	 */
	protected void initSupportedIntensityMeasureParams() {

		DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
		for (int i = 1; i < ZhaoEtAl2006Constants.PERIOD.length; i++) {
			periodConstraint.addDouble(new Double(
					ZhaoEtAl2006Constants.PERIOD[i]));
		}
		periodConstraint.setNonEditable();
		saPeriodParam = new PeriodParam(periodConstraint);

		saDampingParam = new DampingParam();

		saParam = new SA_Param(saPeriodParam, saDampingParam);
		saParam.setNonEditable();

		pgaParam = new PGA_Param();
		pgaParam.setNonEditable();

		saParam.addParameterChangeWarningListener(warningListener);
		pgaParam.addParameterChangeWarningListener(warningListener);

		supportedIMParams.clear();
		supportedIMParams.addParameter(saParam);
		supportedIMParams.addParameter(pgaParam);
	}

	/**
	 * Initialize earthquake rupture parameter (moment magnitude, tectonic
	 * region type, focal depth, rake angle) and add to eqkRuptureParams list.
	 * Makes the parameters non-editable.
	 */
	protected void initEqkRuptureParams() {

		magParam = new MagParam(ZhaoEtAl2006Constants.MAG_WARN_MIN,
				ZhaoEtAl2006Constants.MAG_WARN_MAX);

		StringConstraint options = new StringConstraint();
		options.addString(TectonicRegionType.ACTIVE_SHALLOW.toString());
		options.addString(TectonicRegionType.SUBDUCTION_INTERFACE.toString());
		options.addString(TectonicRegionType.SUBDUCTION_SLAB.toString());
		tectonicRegionTypeParam = new TectonicRegionTypeParam(options,
				TectonicRegionType.ACTIVE_SHALLOW.toString());

		// focal depth (default zero km)
		focalDepthParam = new FocalDepthParam();

		// rake angle (default zero);
		rakeParam = new RakeParam();

		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(tectonicRegionTypeParam);
		eqkRuptureParams.addParameter(focalDepthParam);
		eqkRuptureParams.addParameter(rakeParam);

	}

	/**
	 * Initialize site parameters (vs30) and adds it to the siteParams list.
	 * Makes the parameters non-editable.
	 */
	protected void initSiteParams() {

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
	protected void initPropagationEffectParams() {
		distanceRupParam = new DistanceRupParameter(0.0);
		distanceRupParam.addParameterChangeWarningListener(warningListener);
		DoubleConstraint warn = new DoubleConstraint(
				ZhaoEtAl2006Constants.DISTANCE_RUP_WARN_MIN,
				ZhaoEtAl2006Constants.DISTANCE_RUP_WARN_MAX);
		warn.setNonEditable();
		distanceRupParam.setWarningConstraint(warn);

		distanceRupParam.setNonEditable();
		propagationEffectParams.addParameter(distanceRupParam);
	}

	/**
	 * Initialize other Parameters (standard deviation type, component, sigma
	 * truncation type, sigma truncation level).
	 */
	protected void initOtherParams() {

		sigmaTruncTypeParam = new SigmaTruncTypeParam();
		sigmaTruncLevelParam = new SigmaTruncLevelParam();

		StringConstraint stdDevTypeConstraint = new StringConstraint();
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
		stdDevTypeConstraint.setNonEditable();
		stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

		StringConstraint constraint = new StringConstraint();
		constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
		constraint.addString(ComponentParam.COMPONENT_GMRotI50);
		constraint.setNonEditable();
		componentParam = new ComponentParam(constraint,
				ComponentParam.COMPONENT_AVE_HORZ);

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
	protected void initIndependentParamLists() {

		// params that the mean depends upon
		meanIndependentParams.clear();
		meanIndependentParams.addParameter(magParam);
		meanIndependentParams.addParameter(focalDepthParam);
		meanIndependentParams.addParameter(tectonicRegionTypeParam);
		meanIndependentParams.addParameter(distanceRupParam);
		meanIndependentParams.addParameter(vs30Param);
		meanIndependentParams.addParameter(rakeParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(saPeriodParam);
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
	protected void initParameterEventListeners() {
		// earthquake rupture params
		magParam.addParameterChangeListener(this);
		tectonicRegionTypeParam.addParameterChangeListener(this);
		focalDepthParam.addParameterChangeListener(this);
		rakeParam.addParameterChangeListener(this);

		// site params
		vs30Param.addParameterChangeListener(this);

		// propagation effect param
		distanceRupParam.addParameterChangeListener(this);

		// standard deviation type param
		stdDevTypeParam.addParameterChangeListener(this);
	}

	/**
	 * This sets the eqkRupture related parameters (moment magnitude, tectonic
	 * region type, focal depth, rake angle) based on the eqkRupture passed in.
	 * The internally held eqkRupture object is also set as that passed in.
	 * Warning constrains on magnitude and focal depth are ignored.
	 */
	public void setEqkRupture(EqkRupture eqkRupture)
			throws InvalidRangeException {

		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

		if (eqkRupture.getTectRegType() != null) {
			tectonicRegionTypeParam.setValue(eqkRupture.getTectRegType()
					.toString());
		} else {
			throw new RuntimeException("Tectonic region type not set in "
					+ " earthquake rupture");
		}

		if (eqkRupture.getHypocenterLocation() != null) {
			focalDepthParam.setValueIgnoreWarning(new Double(eqkRupture
					.getHypocenterLocation().getDepth()));
		} else {
			throw new RuntimeException("Hypocenter location not set in"
					+ " earthquake rupture");
		}

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
	 * This sets the site and eqkRupture, and the related parameters, from the
	 * propEffect object passed in.
	 */
	public void setPropagationEffectParams() {
		if ((this.site != null) && (this.eqkRupture != null)) {
			distanceRupParam.setValue(eqkRupture, site);
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

		if (rRup > USER_MAX_DISTANCE) {
			return VERY_SMALL_MEAN;
		}
		setPeriodIndex();
		return getMean(iper, mag, rRup, focalDepth, rake, vs30, tecRegType);
	}

	/**
	 * Compute standard deviation.
	 */
	public double getStdDev() {

		setPeriodIndex();
		return getStdDev(iper, stdDevType, tecRegType);
	}

	/**
	 * Allows the user to set the default parameter values for the selected
	 * Attenuation Relationship.
	 */
	public void setParamDefaults() {

		magParam.setValueAsDefault();
		tectonicRegionTypeParam.setValueAsDefault();
		focalDepthParam.setValueAsDefault();
		rakeParam.setValueAsDefault();
		vs30Param.setValueAsDefault();
		distanceRupParam.setValueAsDefault();
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
	public String getName() {
		return NAME;
	}

	/**
	 * Returns the Short Name.
	 * 
	 */
	public String getShortName() {
		return SHORT_NAME;
	}

	/**
	 * Compute mean (natural logarithm of median ground motion).
	 */
	public double getMean(int iper, double mag, double rRup, double hypodepth,
			double rake, double vs30, String tectonicRegiontType) {
		
		// to avoid zero distances
		if(rRup==0){
			rRup = 0.1;
		}

		// This is unity for reverse crustal events - Otherwise 0
		double flag_Fr = 0.0;
		// This is unity for crustal events - Otherwise 0
		double flag_sc = 0.0;
		// This is unity for interface events - Otherwise 0
		double flag_Si = 0.0;
		// This is unity for slab events - Otherwise 0
		double flag_Ss = 0.0;
		// This is unity for slab events - Otherwise 0
		double flag_Ssl = 0.0;

		double hc = 125;
		double hlow = 15; // see bottom of left column page 902
		double delta_h = 0.0;
		double mc;
		double pFa = 0.0;
		double qFa = 0.0;
		double wFa = 0.0;
		double m2CorrFact = 0.0;

		double soilCoeff = setSiteTermCorrection(iper, vs30);

		// Setting the flags in order to account for tectonic region and focal
		// mechanism
		if (rake > 30
				&& rake < 150
				&& tectonicRegiontType
						.equalsIgnoreCase(TectonicRegionType.ACTIVE_SHALLOW
								.toString())) {
			flag_Fr = 1.0;
			mc = 6.3;
			pFa = 0.0;
			qFa = ZhaoEtAl2006Constants.Qc[iper];
			wFa = ZhaoEtAl2006Constants.Wc[iper];
		} else if (tectonicRegiontType
				.equalsIgnoreCase(TectonicRegionType.ACTIVE_SHALLOW.toString())) {
			flag_sc = 1.0;
			mc = 6.3;
			pFa = 0.0;
			qFa = ZhaoEtAl2006Constants.Qc[iper];
			wFa = ZhaoEtAl2006Constants.Wc[iper];
		} else if (tectonicRegiontType
				.equalsIgnoreCase(TectonicRegionType.SUBDUCTION_INTERFACE
						.toString())) {
			flag_Si = 1.0;
			mc = 6.3;
			pFa = 0.0;
			qFa = ZhaoEtAl2006Constants.Qi[iper];
			wFa = ZhaoEtAl2006Constants.Wi[iper];
		} else if (tectonicRegiontType
				.equalsIgnoreCase(TectonicRegionType.SUBDUCTION_SLAB.toString())) {
			flag_Ss = 1.0;
			flag_Ssl = 1.0;
			mc = 6.5;
			pFa = ZhaoEtAl2006Constants.Ps[iper];
			qFa = ZhaoEtAl2006Constants.Qs[iper];
			wFa = ZhaoEtAl2006Constants.Ws[iper];
		} else {
			throw new RuntimeException(
					"\n  Cannot handle this combination: \n  tectonic region + focal mechanism ");
		}

		if (hypodepth > hlow) {
			delta_h = 1;
			if (hypodepth < hc) {
				hypodepth = hypodepth - hlow;
			} else {
				hypodepth = hc - hlow;
			}
		} else {
			delta_h = 0;
		}

		// Correction factor
		m2CorrFact = pFa * (mag - mc) + qFa * Math.pow((mag - mc), 2.0) + wFa;

		double r = rRup + ZhaoEtAl2006Constants.C[iper]
				* Math.exp(ZhaoEtAl2006Constants.D[iper] * mag);

		double lnGm = ZhaoEtAl2006Constants.A[iper] * mag
				+ ZhaoEtAl2006Constants.B[iper] * rRup - Math.log(r)
				+ ZhaoEtAl2006Constants.E[iper] * hypodepth * delta_h + flag_Fr
				* ZhaoEtAl2006Constants.Sr[iper] + flag_Si
				* ZhaoEtAl2006Constants.Si[iper] + flag_Ss
				* ZhaoEtAl2006Constants.Ss[iper] 
				+ soilCoeff;

		lnGm = lnGm + flag_Ssl * ZhaoEtAl2006Constants.Ssl[iper] * Math.log(rRup);

		// Return the computed mean value
		lnGm += m2CorrFact;

		// Convert form cm/s2 to g
		return Math.log(Math.exp(lnGm) / 981);
	}

	private double setSiteTermCorrection(int iper, double vs30) {
		double soilCoeff = 0.0;
		if (vs30 > 1100) {
			soilCoeff = ZhaoEtAl2006Constants.Ch[iper];
		} else if (vs30 > 600 && vs30 <= 1100) {
			soilCoeff = ZhaoEtAl2006Constants.C1[iper];
		} else if (vs30 > 300 && vs30 <= 600) {
			soilCoeff = ZhaoEtAl2006Constants.C2[iper];
		} else if (vs30 > 200 && vs30 <= 300) {
			soilCoeff = ZhaoEtAl2006Constants.C3[iper];
		} else if (vs30 <= 200) {
			soilCoeff = ZhaoEtAl2006Constants.C4[iper];
		}
		return soilCoeff;
	}

	/**
	 * This gets the standard deviation for specific parameter settings.
	 */
	public double getStdDev(int iper, String stdDevType, String tecRegType) {

		if (tecRegType.equals(TectonicRegionType.ACTIVE_SHALLOW.toString())) {
			if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				return Math.sqrt(ZhaoEtAl2006Constants.Tau_c[iper]
						* ZhaoEtAl2006Constants.Tau_c[iper]
						+ ZhaoEtAl2006Constants.sigma[iper]
						* ZhaoEtAl2006Constants.sigma[iper]);
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				return 0;
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				return ZhaoEtAl2006Constants.sigma[iper];
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				return ZhaoEtAl2006Constants.Tau_c[iper];
			else
				throw new RuntimeException("Standard deviation type: "
						+ stdDevType + " not recognized");
		} else if (tecRegType.equals(TectonicRegionType.SUBDUCTION_INTERFACE
				.toString())) {
			if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				return Math.sqrt(ZhaoEtAl2006Constants.Tau_i[iper]
						* ZhaoEtAl2006Constants.Tau_i[iper]
						+ ZhaoEtAl2006Constants.sigma[iper]
						* ZhaoEtAl2006Constants.sigma[iper]);
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				return 0;
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				return ZhaoEtAl2006Constants.sigma[iper];
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				return ZhaoEtAl2006Constants.Tau_i[iper];
			else
				throw new RuntimeException("Standard deviation type: "
						+ stdDevType + " not recognized");
		} else if (tecRegType.equals(TectonicRegionType.SUBDUCTION_SLAB
				.toString())) {
			if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				return Math.sqrt(ZhaoEtAl2006Constants.Tau_s[iper]
						* ZhaoEtAl2006Constants.Tau_s[iper]
						+ ZhaoEtAl2006Constants.sigma[iper]
						* ZhaoEtAl2006Constants.sigma[iper]);
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				return 0;
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				return ZhaoEtAl2006Constants.sigma[iper];
			else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				return ZhaoEtAl2006Constants.Tau_s[iper];
			else
				throw new RuntimeException("Standard deviation type: "
						+ stdDevType + " not recognized");
		} else
			throw new RuntimeException("Tectonic region type: " + tecRegType
					+ " not recognized");
	}

	/**
	 * This listens for parameter changes and updates the primitive parameters
	 * accordingly
	 * 
	 * @param e
	 *            ParameterChangeEvent
	 */
	public void parameterChange(ParameterChangeEvent e) {

		String pName = e.getParameterName();
		Object val = e.getNewValue();

		if (pName.equals(MagParam.NAME)) {
			mag = ((Double) val).doubleValue();
		} else if (pName.equals(DistanceRupParameter.NAME)) {
			rRup = ((Double) val).doubleValue();
		} else if (pName.equals(FocalDepthParam.NAME)) {
			focalDepth = ((Double) val).doubleValue();
		} else if (pName.equals(Vs30_Param.NAME)) {
			vs30 = ((Double) val).doubleValue();
		} else if (pName.equals(RakeParam.NAME)) {
			rake = ((Double) val).doubleValue();
		} else if (pName.equals(TectonicRegionTypeParam.NAME)) {
			tecRegType = val.toString();
		} else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = val.toString();
		}
	}

	/**
	 * Allows to reset the change listeners on the parameters.
	 */
	public void resetParameterEventListeners() {
		magParam.removeParameterChangeListener(this);
		distanceRupParam.removeParameterChangeListener(this);
		focalDepthParam.removeParameterChangeListener(this);
		rakeParam.removeParameterChangeListener(this);
		vs30Param.removeParameterChangeListener(this);
		tectonicRegionTypeParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}

	/**
	 * This provides a URL where more info on this model can be obtained.
	 * Currently returns null because no URL has been defined.
	 */
	public URL getInfoURL() throws MalformedURLException {
		return null;
	}
}