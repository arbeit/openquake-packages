package org.opensha.sha.imr.attenRelImpl.constants;

public class FS2011Constants {

	/**
	 * Minimum magnitude.
	 */
	public static final Double MAG_WARN_MIN = new Double(4.79);
	/**
	 * Maximum magnitude.
	 */
	public static final Double MAG_WARN_MAX = new Double(7.9);
	/**
	 * Minimum rupture distance.
	 */
	public static final Double DISTANCE_RUP_WARN_MIN = new Double(0.07);
	/**
	 * Maximum rupture distance (rough).
	 */
	public static final Double DISTANCE_RUP_WARN_MAX = new Double(100.0);
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle minimum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_LOWER =  22.50;
	/**
	 * REVERSE - STYLE of FAULTING (Definition based on rake angle maximum value)  
	 */	
	public static final double FLT_TYPE_REVERSE_RAKE_UPPER =  112.50;
}
