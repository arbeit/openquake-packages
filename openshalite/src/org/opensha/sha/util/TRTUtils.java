package org.opensha.sha.util;

import java.util.HashMap;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class TRTUtils {

    /**
     * This wraps a single IMR in a HashMap with a single TRT, Active Shallow.
     * 
     * @param imr
     * @return
     */
    public static
            HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>
            wrapInHashMap(ScalarIntensityMeasureRelationshipAPI imr) {
        HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap =
                new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
        // The type of tectonic region here is of no consequence (it just a
        // dummy value)
        imrMap.put(TectonicRegionType.ACTIVE_SHALLOW, imr);
        return imrMap;
    }
}
