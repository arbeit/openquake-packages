package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import java.io.Serializable;
import java.util.Arrays;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This holds data for a grid source (single location).
 */
public class GEMPointSourceData extends GEMSourceData implements Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    // this holds the MagFreqDists, FocalMechs, and location.
    private HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc;
    // the following specifies the average depth to top of rupture as a function
    // of magnitude.
    private double[][] aveRupTopVsMag;
    // the following is used to locate small sources (i.e., for all mags lower
    // than the minimum mag in aveRupTopVsMag)
    private double aveHypoDepth;

    /**
	 * 
	 */
    public GEMPointSourceData(String id, String name,
            TectonicRegionType tectReg,
            HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc,
            ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth) {
        this.id = id;
        this.name = name;
        this.tectReg = tectReg;
        this.hypoMagFreqDistAtLoc = hypoMagFreqDistAtLoc;
        int numPoints = aveRupTopVsMag.getNum();
        this.aveRupTopVsMag = new double[numPoints][2];
        for(int i=0;i<numPoints;i++){
        	this.aveRupTopVsMag[i][0] = aveRupTopVsMag.getX(i);
        	this.aveRupTopVsMag[i][1] = aveRupTopVsMag.getY(i);
        }
        this.aveHypoDepth = aveHypoDepth;
    }

    /**
     * 
     * @return
     */
    public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc() {
        return this.hypoMagFreqDistAtLoc;
    }

    /**
     * 
     * @return
     */
    public ArbitrarilyDiscretizedFunc getAveRupTopVsMag() {
    	ArbitrarilyDiscretizedFunc aveRupTopVsMag = 
    		new ArbitrarilyDiscretizedFunc();
        for(int i=0;i<this.aveRupTopVsMag.length;i++){
        	aveRupTopVsMag.set(
        	this.aveRupTopVsMag[i][0],
        	this.aveRupTopVsMag[i][1]);
        }
        return aveRupTopVsMag;
    }

    /**
     * 
     * @return
     */
    public double getAveHypoDepth() {
        return this.aveHypoDepth;
    }
    
    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof GEMPointSourceData))
        {
            return false;
        }

        GEMPointSourceData other = (GEMPointSourceData) obj;

        return id.equals(other.id) && name.equals(other.name)
                && tectReg.equals(other.tectReg)
                && hypoMagFreqDistAtLoc.equals(other.hypoMagFreqDistAtLoc) 
                && Arrays.deepEquals(aveRupTopVsMag, other.aveRupTopVsMag)
                && aveHypoDepth == other.aveHypoDepth;
    }
}
