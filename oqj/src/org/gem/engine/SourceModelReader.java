package org.gem.engine;

import java.io.File;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import org.dom4j.Document;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Class for reading source model data in a nrML format file. The constructor of
 * this class takes the path of the file to read from.
 * 
 */
public class SourceModelReader {

    private final List<GEMSourceData> sourceList;

    private final String path;
    private final double deltaMFD;

    // border type for area source definition
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    private static String SIMPLE_FAULT = "simpleFault";
    private static String COMPLEX_FAULT = "complexFault";
    private static String AREA = "area";
    private static String POINT = "point";

    private static String SOURCE_NAME = "sourceName";
    private static String SOURCE_ID = "sourceID";
    private static String TECTONIC_REGION = "tectonicRegion";

    private static String SIMPLE_FAULT_GEOMETRY = "simpleFaultGeometry";
    private static String FAULT_TRACE = "faultTrace";
    private static String UPPER_SEIMSMOGENIC_DEPTH = "upperSeismogenicDepth";
    private static String LOWER_SEISMOGENIC_DEPTH = "lowerSeismogenicDepth";

    private static String COMPLEX_FAULT_GEOMETRY = "complexFaultGeometry";
    private static String FAULT_TOP_EDGE = "faultTopEdge";
    private static String FAULT_BOTTOM_EDGE = "faultBottomEdge";

    private static String AREA_BOUNDARY = "areaBoundary";
    private static String EXTERIOR = "exterior";
    private static String LINEAR_RING = "LinearRing";
    private static String POS_LIST = "posList";

    private static String POINT_LOCATION = "pointLocation";
    private static String POS = "pos";

    private static String RUPTURE_RATE_MODEL = "ruptureRateModel";

    private static String HYPOCENTRAL_DEPTH = "hypocentralDepth";

    private static String FOCAL_MECHANISM = "focalMechanism";
    private static String STRIKE = "strike";
    private static String DIP = "dip";
    private static String RAKE = "rake";

    private static String RUPTURE_DEPTH_DISTRIBUTION =
            "ruptureDepthDistribution";
    private static String XVALUES = "XValues";
    private static String YVALUES = "YValues";

    private static String EVENLY_DISCRETIZED_MAG_FREQ_DIST =
            "evenlyDiscretizedIncrementalMagFreqDist";
    private static String BIN_SIZE = "binSize";
    private static String MIN_VAL = "minVal";
    private static String BIN_COUNT = "binCount";
    private static String DISTRIBUTION_VALUES = "DistributionValues";

    private static String TRUNCATED_GUTENBERG_RICHTER =
            "truncatedGutenbergRichter";
    private static String a_VALUE_CUMULATIVE = "aValueCumulative";
    private static String b_VALUE = "bValue";
    private static String MIN_MAGNITUDE = "minMagnitude";
    private static String MAX_MAGNITUDE = "maxMagnitude";

    /**
     * Creates a new SourceModelReader given the path of the file to read from
     * and the bin width for the magnitude frequency distribution definition
     */
    public SourceModelReader(String path, double deltaMFD) {
        this.path = path;
        this.sourceList = new ArrayList<GEMSourceData>();
        this.deltaMFD = deltaMFD;
    }

    /**
     * Reads file and returns source model data. For each source definition, a
     * {@link GEMSourceData} is created and stored in a list.
     */
    public List<GEMSourceData> read() {

        File xml = new File(path);
        SAXReader reader = new SAXReader();
        Document doc = null;
        try {
            doc = reader.read(xml);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        Element root = doc.getRootElement();
        Iterator i = root.elements().iterator();
        while (i.hasNext()) {
            Element elem = (Element) i.next();
            String elemName = elem.getName();
            if (elemName.equalsIgnoreCase(SIMPLE_FAULT)) {
                sourceList.add(getSimpleFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(COMPLEX_FAULT)) {
                sourceList.add(getComplexFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(AREA)) {
                sourceList.add(getAreaSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(POINT)) {
                sourceList.add(getPointSourceData(deltaMFD, elem));
            }
        }
        return sourceList;
    }

    /**
     * Reads and return point source data
     */
    private GEMPointSourceData
            getPointSourceData(double deltaMFD, Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Location pointLoc = getPointLocation(elem.element(POINT_LOCATION));
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                getMagFreqDistsForFocalMechs(deltaMFD, elem);
        HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc =
                new HypoMagFreqDistAtLoc(
                        magfreqDistFocMech.getMagFreqDistList(), pointLoc,
                        magfreqDistFocMech.getFocalMechanismList());
        ArbitrarilyDiscretizedFunc rupDepthDist =
                getRuptureDepthDistribution(elem
                        .element(RUPTURE_DEPTH_DISTRIBUTION));
        double hypocentralDepth =
                Double.valueOf((String) elem.element(HYPOCENTRAL_DEPTH)
                        .getData());
        return new GEMPointSourceData(srcID, srcName, tectRegType,
                hypoMagFreqDistAtLoc, rupDepthDist, hypocentralDepth);
    }

    /**
     * Reads and returns area source data
     */
    private GEMAreaSourceData getAreaSourceData(double deltaMFD, Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Region reg =
                new Region(get2DLocList(elem.element(AREA_BOUNDARY)
                        .element(EXTERIOR).element(LINEAR_RING)
                        .element(POS_LIST)), borderType);
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                getMagFreqDistsForFocalMechs(deltaMFD, elem);
        ArbitrarilyDiscretizedFunc rupDepthDist =
                getRuptureDepthDistribution(elem
                        .element(RUPTURE_DEPTH_DISTRIBUTION));
        double hypocentralDepth =
                Double.valueOf((String) elem.element(HYPOCENTRAL_DEPTH)
                        .getData());
        return new GEMAreaSourceData(srcID, srcName, tectRegType, reg,
                magfreqDistFocMech, rupDepthDist, hypocentralDepth);
    }

    /**
     * Reads and returns complex fault source data
     */
    private GEMSubductionFaultSourceData getComplexFaultSourceData(
            double deltaMFD, Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Element complexFaultGeometry = elem.element(COMPLEX_FAULT_GEOMETRY);
        FaultTrace faultTopEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_TOP_EDGE)
                        .element(POS_LIST));
        FaultTrace faultBottomEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_BOTTOM_EDGE)
                        .element(POS_LIST));
        double rake = Double.valueOf((String) elem.element(RAKE).getData());
        IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, elem);
        return new GEMSubductionFaultSourceData(srcID, srcName, tectRegType,
                faultTopEdge, faultBottomEdge, rake, magFreqDist, true);
    }

    /**
     * Reads and return simple fault source data
     */
    private GEMFaultSourceData getSimpleFaultSourceData(double deltaMFD,
            Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Element simpleFaultGeometry = elem.element(SIMPLE_FAULT_GEOMETRY);
        FaultTrace faultTrace =
                getFaultTrace(simpleFaultGeometry.element(FAULT_TRACE).element(
                        POS_LIST));
        double dip =
                Double.valueOf((String) simpleFaultGeometry.element(DIP)
                        .getData());
        double upperSeismogenicDepth =
                Double.valueOf((String) simpleFaultGeometry.element(
                        UPPER_SEIMSMOGENIC_DEPTH).getData());
        double lowerSeismogenicDepth =
                Double.valueOf((String) simpleFaultGeometry.element(
                        LOWER_SEISMOGENIC_DEPTH).getData());
        double rake = Double.valueOf((String) elem.element(RAKE).getData());
        IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, elem);
        return new GEMFaultSourceData(srcID, srcName, tectRegType, magFreqDist,
                faultTrace, dip, rake, lowerSeismogenicDepth,
                upperSeismogenicDepth, true);
    }

    /**
     * Reads fault trace coordinates (Each point being specified by a triplet
     * (longitude, latitude, depth)) and returns {@link FaultTrace}
     */
    private FaultTrace getFaultTrace(Element trace) {
        FaultTrace faultTrace = new FaultTrace("");
        LocationList locList = get3DLocList(trace);
        faultTrace.addAll(locList);
        return faultTrace;
    }

    /**
     * Reads magnitude frequency distribution/focal mechanism pairs and returns
     * {@link MagFreqDistsForFocalMechs}
     */
    private MagFreqDistsForFocalMechs getMagFreqDistsForFocalMechs(
            double deltaMFD, Element elem) {
        List<IncrementalMagFreqDist> mfdList =
                new ArrayList<IncrementalMagFreqDist>();
        List<FocalMechanism> focMechList = new ArrayList<FocalMechanism>();
        for (Iterator j = elem.elementIterator(RUPTURE_RATE_MODEL); j.hasNext();) {
            Element e = (Element) j.next();
            IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, e);
            mfdList.add(magFreqDist);
            FocalMechanism focMech =
                    getFocalMechanism(e.element(FOCAL_MECHANISM));
            focMechList.add(focMech);
        }
        IncrementalMagFreqDist[] mfdArray =
                new IncrementalMagFreqDist[mfdList.size()];
        FocalMechanism[] fmArray = new FocalMechanism[focMechList.size()];
        for (int ii = 0; ii < mfdList.size(); ii++) {
            mfdArray[ii] = mfdList.get(ii);
            fmArray[ii] = focMechList.get(ii);
        }
        return new MagFreqDistsForFocalMechs(mfdArray, fmArray);
    }

    /**
     * Reads magnitude frequency distribution data (truncated Gutenberg-Richter
     * or incremental evenly discretized) and returns
     * {@link IncrementalMagFreqDist}
     */
    private IncrementalMagFreqDist
            getMagFreqDist(double deltaMFD, Element elem) {
        IncrementalMagFreqDist magFreqDist = null;
        if (elem.element(TRUNCATED_GUTENBERG_RICHTER) != null) {
            magFreqDist =
                    getGutenbergRichterMagFreqDist(deltaMFD,
                            elem.element(TRUNCATED_GUTENBERG_RICHTER));
        } else if (elem.element(EVENLY_DISCRETIZED_MAG_FREQ_DIST) != null) {
            magFreqDist =
                    getEvenlyDiscretizedMagFreqDist(elem
                            .element(EVENLY_DISCRETIZED_MAG_FREQ_DIST));
        }
        return magFreqDist;
    }

    /**
     * Reads incremental evenly discretized magnitude frequency distribution
     * data and returns {@link IncrementalMagFreqDist}
     */
    private IncrementalMagFreqDist getEvenlyDiscretizedMagFreqDist(
            Element evenlyDiscretizedMagFreqDist) {
        IncrementalMagFreqDist magFreqDist;
        double binSize =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(BIN_SIZE));
        double minVal =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(MIN_VAL));
        int binCount =
                Integer.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(BIN_COUNT));
        Element distributionValues =
                evenlyDiscretizedMagFreqDist.element(DISTRIBUTION_VALUES);
        magFreqDist = new IncrementalMagFreqDist(minVal, binCount, binSize);
        String occurrenceRates = (String) distributionValues.getData();
        StringTokenizer st = new StringTokenizer(occurrenceRates);
        int index = 0;
        while (st.hasMoreTokens()) {
            magFreqDist.add(index, Double.valueOf(st.nextToken()));
            index = index + 1;
        }
        return magFreqDist;
    }

    /**
     * Reads Gutenberg-Richter magnitude frequency distribution data and returns
     * {@link GutenbergRichterMagFreqDist}
     */
    private GutenbergRichterMagFreqDist getGutenbergRichterMagFreqDist(
            double deltaMFD, Element gutenbergRichter) {
        GutenbergRichterMagFreqDist magFreqDist;
        double aVal =
                Double.valueOf((String) gutenbergRichter.element(
                        a_VALUE_CUMULATIVE).getData());
        double bVal =
                Double.valueOf((String) gutenbergRichter.element(b_VALUE)
                        .getData());
        double minMag =
                Double.valueOf((String) gutenbergRichter.element(MIN_MAGNITUDE)
                        .getData());
        double maxMag =
                Double.valueOf((String) gutenbergRichter.element(MAX_MAGNITUDE)
                        .getData());
        magFreqDist = createGrMfd(aVal, bVal, minMag, maxMag, deltaMFD);
        return magFreqDist;
    }

    /**
     * Reads focal mechanism data (strike, dip and rake) and returns
     * {@link FocalMechanism}
     */
    private FocalMechanism getFocalMechanism(Element focalMech) {
        double strike =
                Double.valueOf((String) focalMech.element(STRIKE).getData());
        double dip = Double.valueOf((String) focalMech.element(DIP).getData());
        double rake =
                Double.valueOf((String) focalMech.element(RAKE).getData());
        return new FocalMechanism(strike, dip, rake);
    }

    /**
     * Reads rupture depth distribution data (rupture magnitude vs. rupture
     * depth) and returns an {@link ArbitrarilyDiscretizedFunc}
     */
    private ArbitrarilyDiscretizedFunc getRuptureDepthDistribution(
            Element ruptureDepthDist) {
        ArbitrarilyDiscretizedFunc rupDepthDist =
                new ArbitrarilyDiscretizedFunc();
        String xVals = (String) ruptureDepthDist.element(XVALUES).getData();
        String yVals = (String) ruptureDepthDist.element(YVALUES).getData();
        StringTokenizer xVal = new StringTokenizer(xVals);
        StringTokenizer yVal = new StringTokenizer(yVals);
        while (xVal.hasMoreTokens())
            rupDepthDist.set(Double.valueOf(xVal.nextToken()),
                    Double.valueOf(yVal.nextToken()));
        return rupDepthDist;
    }

    /**
     * Reads location list (each location being specified by a triplet
     * (longitude,latitude,depth)) and returns {@link LocationList}
     */
    private LocationList get3DLocList(Element posList) {
        LocationList locList = new LocationList();
        String positionList = (String) posList.getData();
        StringTokenizer st = new StringTokenizer(positionList);
        while (st.hasMoreTokens()) {
            double lon = Double.valueOf(st.nextToken());
            double lat = Double.valueOf(st.nextToken());
            double depth = Double.valueOf(st.nextToken());
            locList.add(new Location(lat, lon, depth));
        }
        return locList;
    }

    /**
     * Reads location list (each location being specified by a doublet
     * (longitude,latitude)) and returns a {@link LocationList}
     */
    private LocationList get2DLocList(Element posList) {
        LocationList locList = new LocationList();
        String positionList = (String) posList.getData();
        StringTokenizer st = new StringTokenizer(positionList);
        while (st.hasMoreTokens()) {
            double lon = Double.valueOf(st.nextToken());
            double lat = Double.valueOf(st.nextToken());
            locList.add(new Location(lat, lon));
        }
        return locList;
    }

    /**
     * Reads single location (longitude,latitude). Returns {@link Location}
     */
    private Location getPointLocation(Element pointLocation) {
        String pointCoords = (String) pointLocation.element(POS).getData();
        StringTokenizer st = new StringTokenizer(pointCoords);
        double longitude = Double.valueOf(st.nextToken());
        double latitude = Double.valueOf(st.nextToken());
        return new Location(latitude, longitude);
    }

    /**
     * Defines truncated Gutenberg-Richter magnitude frequency distribution
     * 
     * @param aVal
     *            : cumulative a value
     * @param bVal
     *            : b value
     * @param mMin
     *            : minimum magnitude
     * @param mMax
     *            : maximum magnitude
     * @param deltaMFD
     *            : discretization interval
     * @return {@link GutenbergRichterMagFreqDist}
     */
    private GutenbergRichterMagFreqDist createGrMfd(double aVal, double bVal,
            double mMin, double mMax, double deltaMFD) {
        GutenbergRichterMagFreqDist mfd = null;
        // round mMin and mMax with respect to delta bin
        mMin = Math.round(mMin / deltaMFD) * deltaMFD;
        mMax = Math.round(mMax / deltaMFD) * deltaMFD;
        // compute total cumulative rate between minimum and maximum magnitude
        double totCumRate = Double.NaN;
        if (mMin != mMax) {
            totCumRate =
                    Math.pow(10, aVal - bVal * mMin)
                            - Math.pow(10, aVal - bVal * mMax);
        } else {
            // compute incremental a value and calculate rate corresponding to
            // minimum magnitude
            double aIncr = aVal + Math.log10(bVal * Math.log(10));
            totCumRate = Math.pow(10, aIncr - bVal * mMin);
        }
        if (mMax != mMin) {
            // shift to bin center
            mMin = mMin + deltaMFD / 2;
            mMax = mMax - deltaMFD / 2;
        }
        int numVal = (int) Math.round(((mMax - mMin) / deltaMFD + 1));
        mfd =
                new GutenbergRichterMagFreqDist(bVal, totCumRate, mMin, mMax,
                        numVal);
        return mfd;
    }
}
