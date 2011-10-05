package org.opensha.sha.imr.attenRelImpl.constants;

public class StaffordEtAl2009Constants {

	/**
	 * Minimum magnitude.
	 */
	public static final Double MAG_WARN_MIN = new Double(5.08);
	/**
	 * Maximum magnitude.
	 */
	public static final Double MAG_WARN_MAX = new Double(7.51);
	/**
	 * Minimum rupture distance.
	 */
	public static final Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	/**
	 * Maximum rupture distance (rough).
	 */
	public static final Double DISTANCE_RUP_WARN_MAX = new Double(300.0);
	/**
	 * STIFF SOIL Vs30 upper bound
	 */
	public static final double STIFF_SOIL_UPPER_BOUND = 360.0;
	/**
	 * SOFT SOIL Vs30 upper bound
	 */
	public static final double SOFT_SOIL_UPPER_BOUND  = 180.0;
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle minimum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_LOWER =  22.50;
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle maximum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_UPPER =  112.50;
}
