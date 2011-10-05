package org.opensha.sha.imr.attenRelImpl.constants;

public class TravasarouEtAl2003Constants {

	/**
	 * Minimum magnitude.
	 */
	public static final Double MAG_WARN_MIN = new Double(4.7);
	/**
	 * Maximum magnitude.
	 */
	public static final Double MAG_WARN_MAX = new Double(7.6);
	/**
	 * Minimum rupture distance.
	 */
	public static final Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	/**
	 * Maximum rupture distance (rough).
	 */
	public static final Double DISTANCE_RUP_WARN_MAX = new Double(250.0);
	/**
	 * STIFF SOIL Vs30 upper bound
	 */
	public static final double STIFF_SOIL_UPPER_BOUND = 760.0;
	/**
	 * SOFT SOIL Vs30 upper bound
	 */
	public static final double SOFT_SOIL_UPPER_BOUND  = 360.0;
	/**
	 * NORMAL - STYLE of FAULTING (Definition based on rake angle minimum value)  
	 */	
	public static final double FLT_TYPE_NORMAL_RAKE_LOWER =  -112.50;
	/**
	 * NORMAL - STYLE of FAULTING (Definition based on rake angle maximum value)  
	 */	
	public static final double FLT_TYPE_NORMAL_RAKE_UPPER =  -67.50;
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle minimum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_LOWER =  22.50;
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle maximum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_UPPER =  112.50;
}
