package org.opensha.sha.imr.attenRelImpl.constants;

import org.opensha.sha.util.TectonicRegionType;

public class ZhaoEtAl2006Constants {

	public static final double[] PERIOD = { -1.00, 
		    0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 
		    0.70, 0.80, 0.90, 1.00, 1.25, 1.50, 2.00, 2.50, 3.00, 4.00,
		    5.00 };

	public static final double[] A = { 1.250,
		    1.101, 1.076, 1.118, 1.134, 1.147, 1.149, 1.163, 1.200, 1.250, 1.293, 
		    1.336, 1.386, 1.433, 1.479, 1.551, 1.621, 1.694, 1.748, 1.759, 1.826,
		    1.825 };

	public static final double[] B = { -0.00338,
		    -0.00564, -0.00671, -0.00787, -0.00722,	-0.00659, -0.00590, -0.00520, -0.00422, -0.00338, -0.00282,
			-0.00258, -0.00242, -0.00232, -0.00220, -0.00207, -0.00224, -0.00201, -0.00187, -0.00147, -0.00195,
			-0.00237 };

	public static final double[] C = { 0.0060,
		    0.0055, 0.0075, 0.0090, 0.0100, 0.0120, 0.0140, 0.0150, 0.0100, 0.0060, 0.003, 
		    0.0025, 0.0022, 0.0020,	0.0020, 0.0020, 0.0020, 0.0025, 0.0028, 0.0032, 0.004,
		    0.005 };

	public static final double[] D = { 1.00779,
		    1.07967, 1.05984, 1.08274, 1.05292, 1.01360, 0.96638, 0.93427, 0.95880, 1.00779, 1.08773,
		    1.08384, 1.08849, 1.10920, 1.11474, 1.08295, 1.09117, 1.05492, 1.05191,	1.02452, 1.04356,
		    1.06518 };

	public static final double[] E = {  0.01114,
		    0.014120, 0.01463, 0.01423, 0.01509, 0.01462, 0.01459, 0.01458, 0.01257, 0.01114, 0.010190, 
		    0.009790, 0.00944, 0.00972, 0.01005, 0.01003, 0.00928, 0.00833, 0.00776, 0.00644, 0.005900,
		    0.00510 };

	public static final double[] Sr = { 0.2470,
		    0.2509, 0.2513, 0.2403, 0.2506, 0.2601, 0.2690, 0.2590, 0.2479, 0.2470, 0.2326, 
		    0.2200, 0.2321, 0.2196,	0.2107, 0.2510, 0.2483, 0.2631, 0.2620, 0.3066, 0.3529,
		    0.2485 };

	public static final double[] Si = { -0.0528,
		    0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, -0.0412, -0.0528, -0.1034,
		    -0.1460, -0.1638,-0.2062, -0.2393, -0.2557, -0.3065, -0.3214, -0.3366, -0.3306, -0.3898,
		    -0.4978 };

	public static final double[] Ss = { 2.629,
		    2.607, 2.764, 2.156, 2.161, 1.901, 1.814, 2.181, 2.432, 2.629, 2.702, 
		    2.654, 2.480, 2.332, 2.233,	2.029, 1.589, 0.966, 0.789, 1.037, 0.561,
		    0.225 };

	public static final double[] SsZhao = { -0.0448,
		    0.0557, 0.1047, 0.1276, 0.0780, 0.1074, 0.0753, 0.0058, -0.0120, -0.0448, -0.0727,
		   -0.1082,-0.1257, -0.1859, -0.2268, -0.2370, -0.2400, -0.2332, -0.2804,-0.2305, -0.2548,
		   -0.3551 };

	public static final double[] Ssl = {-0.5538,
		    -0.5284, -0.5507, -0.4201, -0.4315, -0.3715, -0.3601, -0.4505, -0.5061, -0.5538, -0.5746,
		    -0.5721, -0.5397, -0.5216, -0.5094, -0.4692, -0.3787, -0.2484, -0.2215,	-0.2625, -0.1689,
		    -0.1201 };

	public static final double[] Sslr = { 2.6292,
		    2.6069, 2.7638, 2.1558, 2.1613, 1.9012, 1.8138, 2.1809, 2.4316, 2.6292, 2.7015, 
		    2.6541, 2.4801,	2.3323, 2.2329, 2.0286, 1.5886, 0.9661, 0.7889, 1.0370, 0.5608,
			0.2248 };

	public static final double[] Ch = { -0.207,
		    0.293, 0.939, 1.499, 1.462, 1.280, 1.121, 0.852, 0.365, -0.207, -0.705, 
		    -1.144, -1.609, -2.023,-2.451, -3.243, -3.888, -4.783, -5.444, -5.839, -6.598,
		    -6.752 };

	public static final double[] C1 = { 0.0713,
		    1.1111, 1.6845, 2.0609, 1.9165, 1.6688, 1.4683, 1.1720, 0.6548, 0.0713, -0.4288,
		    -0.8656, -1.3250, -1.7322, -2.1522, -2.9226, -3.5476, -4.4102, -5.0492, -5.4307, -6.1813,
			-6.3471 };

	public static final double[] C2 = { 0.5149,
		    1.3440, 1.7930, 2.1346, 2.1680, 2.0854, 1.9416, 1.6829, 1.1271, 0.5149, -0.0027,
		    -0.4493, -0.9284, -1.3490, -1.7757, -2.5422, -3.1689, -4.0387, -4.6979, -5.0890, -5.8821,
			-6.0512 };

	public static final double[] C3 = { 0.9339,
		    1.3548, 1.7474, 2.0311, 2.0518, 2.0007, 1.9407, 1.8083, 1.4825, 0.9339, 0.3936,
		    -0.1109, -0.6200, -1.0665,-1.5228, -2.3272, -2.9789, -3.8714, -4.4963, -4.8932, -5.6981,
			-5.8733 };

	public static final double[] C4 = { 0.9549,
		    1.4204, 1.8140, 2.0818, 2.1128, 2.0302, 1.9367, 1.7697, 1.3967, 0.9549, 0.5591,
		    0.1880, -0.2463, -0.6430, -1.0840, -1.9364, -2.6613, -3.6396, -4.3414, -4.7585, -5.5879,
			-5.7984 };

	public static final double[] sigma = { 0.6530,
		    0.6039, 0.6399, 0.6936, 0.7017,	0.6917, 0.6823, 0.6696, 0.6589, 0.6530, 0.6527,
		    0.6516, 0.6467,	0.6525, 0.6570, 0.6601, 0.6640, 0.6694, 0.6706, 0.6671, 0.6468,
			0.6431 };

	public static final double[] tau = { 0.3890,
		    0.3976, 0.4437, 0.4903, 0.4603, 0.4233, 0.3908, 0.3790, 0.3897, 0.3890, 0.4014, 
		    0.4079, 0.4183,	0.4106, 0.4101, 0.4021, 0.4076, 0.4138, 0.4108, 0.3961, 0.3821,
			0.3766 };

	public static final double[] Qc = { -0.0126,
		   0.000, 0.000, 0.000, 0.000, 0.000, 0.0000, 0.0000, 0.0000, -0.0126, -0.0329,
		  -0.0501, -0.065, -0.0781,	-0.0899, -0.1148, -0.1351, -0.1672, -0.1921, -0.2124, -0.2445,
			-0.2694 };

	public static final double[] Wc = { 0.0116,
		    0.0000, 0.0000, 0.0000, 0.000, 0.0000, 0.000, 0.0000, 0.0000, 0.0116, 0.0202,
		    0.0274, 0.0336, 0.0391,	0.044, 0.0545, 0.063, 0.0764, 0.0869, 0.0954, 0.1088,
		    0.1193 };

	public static final double[] Tau_c = { 0.338,
		    0.303, 0.326, 0.342, 0.331, 0.312, 0.298, 0.300, 0.346, 0.338, 0.349,
		    0.351, 0.356, 0.348, 0.338,	0.313, 0.306, 0.283, 0.287, 0.278, 0.273,
		    0.275 };

	public static final double[] Qi = { -0.0632,
		     0.0000, 0.0000, 0.0000, -0.0138, -0.0256, -0.0348, -0.0423, -0.0541, -0.0632, -0.0707,
		    -0.0771,-0.0825, -0.0874, -0.0917, -0.1009, -0.1083, -0.1202, -0.1293, -0.1368, -0.1486,
		    -0.1578 };

	public static final double[] Wi = { 0.0562,
		    0.0000, 0.0000, 0.0000, 0.0286, 0.0352, 0.0403, 0.0445, 0.0511, 0.0562, 0.0604, 
		    0.0639, 0.0670, 0.0697,	0.0721, 0.0772, 0.0814, 0.0880, 0.0931, 0.0972, 0.1038,
		    0.1090 };

	public static final double[] Ps = { 0.1381,
		    0.1392, 0.1636, 0.1690, 0.1669, 0.1631, 0.1588, 0.1544, 0.146, 0.1381, 0.1307,
		    0.1239, 0.1176, 0.1116,	0.106, 0.0933, 0.0821, 0.0628, 0.0465, 0.0322, 0.0083,
		    -0.0117 };

	public static final double[] Qs = {  0.1078,
		    0.1584, 0.1932, 0.2057, 0.1984, 0.1856,	0.1714, 0.1573, 0.1309, 0.1078, 0.0878,
		    0.0705, 0.0556, 0.0426,	0.0314, 0.0093, -0.0062, -0.0235, -0.0287, -0.0261, -0.0065,
		    0.0246 };

	public static final double[] Ws = { -0.0008,
		    -0.0529, -0.0841, -0.0877, -0.0773,	-0.0644, -0.0515, -0.0395, -0.0183, -0.0008, 0.0136,
		     0.0254,  0.0352, 0.0432, 0.0498, 0.0612, 0.0674, 0.0692, 0.0622, 0.0496, 0.0150,
		     -0.0268 };

	public static final double[] Tau_s = { 0.272,
		    0.321, 0.378, 0.420, 0.372, 0.324, 0.294, 0.284, 0.278, 0.272, 0.285,
		    0.29,  0.299, 0.289, 0.286, 0.277, 0.282, 0.300, 0.292, 0.274, 0.281,
		    0.296 };

	public static final double[] Tau_i = { 0.277,
		    0.308, 0.343, 0.403, 0.367, 0.328, 0.289, 0.280, 0.271, 0.277, 0.296,
			0.313, 0.329, 0.324, 0.328,0.339, 0.352, 0.360, 0.356, 0.338, 0.307, 
			0.272 };

	public static final double[] Tau_S = { 0.272,
		    0.321, 0.378, 0.420, 0.372, 0.324, 0.294, 0.284, 0.278, 0.272, 0.285, 
		    0.290, 0.299, 0.289, 0.286,	0.277, 0.282, 0.300, 0.292, 0.274, 0.281,
		    0.296 };

	public static final String SITE_TYPE_INFO = "Geological conditions at the site";
	public static final String SITE_TYPE_NAME = "Zhao et al 2006 Site Type";

	// Hard rock description: Vs30 > 1100m/s calculated from site period
	// ()equivalent of NEHRP Class A
	public static final String SITE_TYPE_HARD_ROCK = "Hard Rock";
	// Rock description: Vs30 > 600m/s calculated from site period (T<2.0sec)
	// and equivalent of NEHRP Class A+B
	public static final String SITE_TYPE_ROCK = " Rock";
	// Hard rock description: 300< Vs30 = 600m/s calculated from site period
	// (0.2=T<0.4sec) and equivalent of NEHRP Class C
	public static final String SITE_TYPE_HARD_SOIL = "Hard Soil";
	// Hard rock description: 200< Vs30 = 300m/s calculated from site period
	// (0.4=T<0.6sec) and equivalent of NEHRP Class D
	public static final String SITE_TYPE_MEDIUM_SOIL = "Medium Soil";
	// Hard rock description: Vs30 =200m/s calculated from site period
	// (T=0.6sec) and equivalent of NEHRP Class A
	public static final String SITE_TYPE_SOFT_SOIL = "Soft Soil";
	public static final String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;

	// Style of faulting options
	// Only crustal events with reverse fault mechanism
	public static final String FLT_TEC_ENV_CRUSTAL = TectonicRegionType.ACTIVE_SHALLOW
			.toString();
	public static final String FLT_TEC_ENV_INTERFACE = TectonicRegionType.SUBDUCTION_INTERFACE
			.toString();
	public static final String FLT_TEC_ENV_SLAB = TectonicRegionType.SUBDUCTION_SLAB
			.toString();

	public static final String FLT_FOC_MECH_REVERSE = "Reverse";
	public static final String FLT_FOC_MECH_NORMAL = "Normal";
	public static final String FLT_FOC_MECH_STRIKE_SLIP = "Strike-slip";
	public static final String FLT_FOC_MECH_UNKNOWN = "Unknown";

	public static final Double MAG_WARN_MIN = new Double(5);
	public static final Double MAG_WARN_MAX = new Double(8.3);

	public static final Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	public static final Double DISTANCE_RUP_WARN_MAX = new Double(300.0);
	/**
	 * cm/s/s to g conversion factor.
	 */
	public static final double CMS_TO_G_CONVERSION_FACTOR = 1.0/981.0;
}
