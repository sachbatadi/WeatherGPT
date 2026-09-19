import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { speakText, stopSpeaking } from '../utils/speech';
import { RISK_NODES } from '../data/mockData';
import { RiskNode } from '../types';
import {
  Download,
  Layers,
  RotateCcw,
  Maximize2,
  Flame,
  MapPin,
  ShieldCheck,
  AlertCircle,
  Volume2,
  VolumeX,
  SlidersHorizontal,
} from 'lucide-react';
import L from 'leaflet';

export const RiskMapView: React.FC = () => {
  const { t, language, isSimpleMode, setIsSimpleMode } = useLanguage();
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [mapType, setMapType] = useState<'streets' | 'hybrid' | 'terrain'>('terrain');
  const [isZoomActive, setIsZoomActive] = useState<boolean>(false);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const circlesLayerRef = useRef<L.LayerGroup | null>(null);

  const handleSpeakMap = () => {
    if (isSpeaking) {
      stopSpeaking();
      setIsSpeaking(false);
      return;
    }

    const speechText =
      language === 'pa'
        ? 'ਨਕਸ਼ੇ ਉੱਤੇ ਲਾਲ ਰੰਗ ਦੇ ਨਿਸ਼ਾਨ ਹੜ੍ਹ ਖ਼ਤਰੇ ਵਾਲੇ ਇਲਾਕੇ ਹਨ। ਪੀਲੇ ਨਿਸ਼ਾਨ ਸਾਵਧਾਨੀ ਵਾਲੇ ਹਨ। ਹਰੇ ਰੰਗ ਦੇ ਨਿਸ਼ਾਨ ਸੁਰੱਖਿਅਤ ਰਾਹਤ ਕੈਂਪ ਅਤੇ ਉੱਚੀਆਂ ਥਾਵਾਂ ਹਨ ਜਿੱਥੇ ਤੁਸੀਂ ਪਨਾਹ ਲੈ ਸਕਦੇ ਹੋ।'
        : language === 'hi'
        ? 'मानचित्र पर लाल रंग के निशान बाढ़ के खतरे वाले क्षेत्र हैं। पीले निशान सावधानी क्षेत्र हैं। हरे रंग के निशान सुरक्षित राहत शिविर और स्कूल हैं जहाँ आप शरण ले सकते हैं।'
        : 'On the map, red markers indicate active flood risk zones. Yellow markers indicate alert areas. Green markers indicate designated safe relief camps and high grounds.';

    speakText(
      speechText,
      language,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false)
    );
  };

  const filteredNodes = RISK_NODES.filter((node) => {
    if (filter === 'ALL') return true;
    return node.threatLevel === filter;
  });

  // Initialize Leaflet Map with Google Maps Physical / Terrain Tiles
  // Scroll zoom is initially disabled so scrolling down the page is uninterrupted
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Center on Punjab region (around Jalandhar / Ludhiana / Patiala)
      const map = L.map(mapContainerRef.current, {
        center: [31.25, 75.6],
        zoom: 9,
        scrollWheelZoom: false, // Disabled until clicked to avoid page scroll hijacking
        zoomControl: true,
      });

      // Google Maps Physical / Terrain Mode by default
      const tileLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; Google Maps',
        maxZoom: 20,
      }).addTo(map);

      tileLayerRef.current = tileLayer;

      // On click anywhere on map, enable scroll wheel zoom
      map.on('click', () => {
        setIsZoomActive(true);
        map.scrollWheelZoom.enable();
      });

      const circlesLayer = L.layerGroup().addTo(map);
      circlesLayerRef.current = circlesLayer;

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    // Auto-disable scroll zoom on mouseleave so page scroll resumes smoothly
    const container = mapContainerRef.current;
    const handleMouseLeave = () => {
      setIsZoomActive(false);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.scrollWheelZoom.disable();
      }
    };

    if (container) {
      container.addEventListener('mouseleave', handleMouseLeave);
    }

    return () => {
      if (container) {
        container.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Switch Google Maps Layer Type (Roadmap, Satellite/Hybrid, Terrain)
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    if (tileLayerRef.current) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
    }
    const lyrs = mapType === 'hybrid' ? 'y' : mapType === 'terrain' ? 'p' : 'm';
    const newTileLayer = L.tileLayer(`https://{s}.google.com/vt/lyrs=${lyrs}&x={x}&y={y}&z={z}`, {
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
      attribution: '&copy; Google Maps',
      maxZoom: 20,
    }).addTo(mapInstanceRef.current);
    tileLayerRef.current = newTileLayer;
    newTileLayer.bringToBack();
  }, [mapType]);

  // Invalidate map size on expand
  useEffect(() => {
    if (mapInstanceRef.current) {
      setTimeout(() => {
        mapInstanceRef.current?.invalidateSize();
      }, 200);
    }
  }, [isExpanded]);

  // Update Markers & Circles when filter or language changes
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current || !circlesLayerRef.current) return;

    // 1. Update Circles with localized popups & hover ground scenes
    circlesLayerRef.current.clearLayers();

    const jalandharSceneDesc = `
      <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 250px; padding: 2px; line-height: 1.45;">
        <div style="display: flex; items-center: center; gap: 6px; margin-bottom: 6px; padding-bottom: 5px; border-bottom: 1px solid #fee2e2;">
          <span style="background: #dc2626; color: white; font-weight: 800; font-size: 10px; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.5px;">
            ${language === 'pa' ? '🚨 ਸਰਗਰਮ ਹੜ੍ਹ ਦ੍ਰਿਸ਼' : language === 'hi' ? '🚨 सक्रिय बाढ़ दृश्य' : '🚨 CRITICAL FLOOD INUNDATION'}
          </span>
          <span style="font-size: 11px; color: #dc2626; font-weight: 700;">14 km Radius</span>
        </div>
        <strong style="color: #0f172a; font-size: 13px; display: block; margin-bottom: 3px;">
          ${language === 'pa' ? 'ਜਲੰਧਰ ਸ਼ਹਿਰੀ ਅਤੇ ਨਹਿਰੀ ਡਰੇਨੇਜ ਸੈਕਟਰ' : language === 'hi' ? 'जालंधर शहरी एवं नहर जल निकासी क्षेत्र' : 'Jalandhar Urban & Canal Inundation Sector'}
        </strong>
        <p style="color: #334155; margin: 4px 0 6px 0; font-size: 11.5px;">
          ${
            language === 'pa'
              ? 'ਜ਼ਮੀਨੀ ਸਥਿਤੀ: ਬਸਤੀ ਦਾਨਿਸ਼ਮੰਦਾ ਅਤੇ ਨਹਿਰੀ ਕਾਲੋਨੀ ਵਿੱਚ 1.6 ਮੀਟਰ ਪਾਣੀ ਭਰਿਆ। ਐਸ.ਡੀ.ਆਰ.ਐਫ ਦੀਆਂ 4 ਮੋਟਰਾਈਜ਼ਡ ਕਿਸ਼ਤੀਆਂ ਪਰਿਵਾਰਾਂ ਨੂੰ ਕੱਢ ਰਹੀਆਂ ਹਨ। ਬਿਜਲੀ ਗਰਿੱਡ ਬੰਦ ਹੈ।'
              : language === 'hi'
              ? 'जमीनी स्थिति: बस्ती दानिशमंदा एवं नहर कॉलोनी में 1.6 मीटर जलभराव। एसडीआरएफ की 4 मोटर चालित नावें परिवारों को निकाल रही हैं। बिजली ग्रिड बंद है।'
              : 'Ground Scene: 1.6m water inundating residential streets near Basti Danishmanda canal. 4 SDRF motorized boats actively rescuing marooned families. Power grid safely shut down.'
          }
        </p>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px;">
          <div><span style="color: #64748b;">Water Gauge:</span> <b style="color: #dc2626;">+1.6m Breached</b></div>
          <div><span style="color: #64748b;">Rescue Teams:</span> <b>4 Boat Units</b></div>
          <div><span style="color: #64748b;">Evac Directive:</span> <b style="color: #dc2626;">MANDATORY</b></div>
          <div><span style="color: #64748b;">Safe Camp:</span> <b>Model Town Hub</b></div>
        </div>
      </div>
    `;

    const patialaSceneDesc = `
      <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 250px; padding: 2px; line-height: 1.45;">
        <div style="display: flex; items-center: center; gap: 6px; margin-bottom: 6px; padding-bottom: 5px; border-bottom: 1px solid #fee2e2;">
          <span style="background: #dc2626; color: white; font-weight: 800; font-size: 10px; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.5px;">
            ${language === 'pa' ? '🚨 ਲਾਜ਼ਮੀ ਨਿਕਾਸੀ ਦ੍ਰਿਸ਼' : language === 'hi' ? '🚨 अनिवार्य निकासी दृश्य' : '🚨 MANDATORY EVACUATION'}
          </span>
          <span style="font-size: 11px; color: #dc2626; font-weight: 700;">16 km Radius</span>
        </div>
        <strong style="color: #0f172a; font-size: 13px; display: block; margin-bottom: 3px;">
          ${language === 'pa' ? 'ਪਟਿਆਲਾ ਘੱਗਰ ਤੇ ਵੱਡੀ ਨਦੀ ਜਲ ਗ੍ਰਹਿਣ ਖੇਤਰ' : language === 'hi' ? 'पटियाला घग्गर व बड़ी नदी जलग्रहण क्षेत्र' : 'Patiala Ghaggar & Badi Nadi Basin'}
        </strong>
        <p style="color: #334155; margin: 4px 0 6px 0; font-size: 11.5px;">
          ${
            language === 'pa'
              ? 'ਜ਼ਮੀਨੀ ਸਥਿਤੀ: ਘੱਗਰ ਦਰਿਆ ਖ਼ਤਰੇ ਦੇ ਨਿਸ਼ਾਨ (14.50m) ਤੋਂ ਉੱਪਰ 14.82m \'ਤੇ ਵਹਿ ਰਿਹਾ ਹੈ। ਵਾਰਡ 12-14 ਦੇ ਹੇਠਲੇ ਘਰਾਂ ਵਿੱਚੋਂ 42,000 ਵਸਨੀਕਾਂ ਨੂੰ ਸਰਕਾਰੀ ਮਹਿੰਦਰਾ ਕਾਲਜ ਰਾਹਤ ਕੈਂਪ ਵਿੱਚ ਤਬਦੀਲ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ।'
              : language === 'hi'
              ? 'जमीनी स्थिति: घग्गर नदी खतरे के निशान (14.50m) से ऊपर 14.82m पर बह रही है। वार्ड 12-14 के निचले घरों से 42,000 निवासियों को सरकारी मोहिंद्रा कॉलेज राहत शिविर में भेजा जा रहा है।'
              : 'Ground Scene: Ghaggar river overflowing danger mark at 14.82m. Evacuation of 42,000 residents across Wards 12-14 to Govt Mohindra College relief camp in active progress.'
          }
        </p>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px;">
          <div><span style="color: #64748b;">River Stage:</span> <b style="color: #dc2626;">14.82m (Danger)</b></div>
          <div><span style="color: #64748b;">EPI Priority:</span> <b style="color: #dc2626;">8.4 / 10</b></div>
          <div><span style="color: #64748b;">Bridges:</span> <b>Traffic Closed</b></div>
          <div><span style="color: #64748b;">Shelters:</span> <b>Mohindra & Khalsa</b></div>
        </div>
      </div>
    `;

    const circle1 = L.circle([31.326, 75.576], {
      color: '#dc2626',
      fillColor: '#ef4444',
      fillOpacity: 0.22,
      radius: 14000,
      weight: 2,
    }).addTo(circlesLayerRef.current).bindPopup(jalandharSceneDesc);

    circle1.on('mouseover', function (this: L.Circle) {
      this.openPopup();
    });

    const circle2 = L.circle([30.339, 76.386], {
      color: '#dc2626',
      fillColor: '#ef4444',
      fillOpacity: 0.25,
      radius: 16000,
      weight: 2,
    }).addTo(circlesLayerRef.current).bindPopup(patialaSceneDesc);

    circle2.on('mouseover', function (this: L.Circle) {
      this.openPopup();
    });

    // 2. Update Markers with rich hover & click Ground Scene popups
    layerGroupRef.current.clearLayers();

    const districtLabel = t('map.table.district', 'District');
    const threatHeader = t('map.table.threat', 'Threat');
    const gaugeHeader = t('map.table.capacity', 'Gauge Cap.');
    const capWord = t('common.capacity', 'capacity');
    const rainHeader = t('map.table.rain', 'Precip Rate');
    const directiveHeader = t('map.table.mitigation', 'Directive');

    filteredNodes.forEach((node) => {
      const colorMap = {
        CRITICAL: '#dc2626',
        HIGH: '#ea580c',
        MEDIUM: '#ca8a04',
        LOW: '#16a34a',
      };
      const markerColor = colorMap[node.threatLevel];

      const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="
          background-color: ${markerColor};
          width: 18px;
          height: 18px;
          border-radius: 50%;
          border: 2.5px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
          cursor: pointer;
        "></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      });

      const nodeName = t('node.name.' + node.id, node.name);
      const districtName = t('district.' + node.district, node.district);
      const threatLabel = t('common.' + node.threatLevel.toLowerCase(), node.threatLevel);
      const mitText = t('node.mit.' + node.id, node.mitigation);

      // Scene badge & ground status description
      let sceneBadge = '🚨 ACTIVE INUNDATION SCENE';
      let sceneBadgeBg = '#dc2626';
      let groundScene = 'Streets inundated with rapid surface runoff. Emergency pumps and rescue teams deployed on site.';

      if (node.threatLevel === 'CRITICAL') {
        sceneBadge = language === 'pa' ? '🚨 ਗੰਭੀਰ ਹੜ੍ਹ ਦ੍ਰਿਸ਼' : language === 'hi' ? '🚨 गंभीर बाढ़ दृश्य' : '🚨 CRITICAL INUNDATION SCENE';
        sceneBadgeBg = '#dc2626';
        groundScene =
          language === 'pa'
            ? 'ਪਾਣੀ ਦਾ ਪੱਧਰ ਖ਼ਤਰੇ ਤੋਂ 114%+ ਉੱਪਰ। ਬੰਨ੍ਹਾਂ \'ਤੇ ਰੇਤ ਦੀਆਂ ਬੋਰੀਆਂ ਲਗਾਈਆਂ ਜਾ ਰਹੀਆਂ ਹਨ। ਵਸਨੀਕਾਂ ਦੀ ਨਿਕਾਸੀ ਜਾਰੀ।'
            : language === 'hi'
            ? 'जलस्तर खतरे के निशान से 114%+ ऊपर। तटबंधों पर रेत की बोरियां लगाई जा रही हैं। निवासियों की निकासी जारी।'
            : 'Water level surging beyond 114% capacity. Embankment reinforcement active with sandbagging and mandatory citizen evacuation.';
      } else if (node.threatLevel === 'HIGH') {
        sceneBadge = language === 'pa' ? '⚠️ ਉੱਚ ਚੇਤਾਵਨੀ ਦ੍ਰਿਸ਼' : language === 'hi' ? '⚠️ उच्च चेतावनी दृश्य' : '⚠️ HIGH ALERT SCENE';
        sceneBadgeBg = '#ea580c';
        groundScene =
          language === 'pa'
            ? 'ਸ਼ਿਵਾਲਿਕ ਪਹਾੜੀ ਢਲਾਨਾਂ ਤੋਂ ਤੇਜ਼ ਚੋਅ ਦਾ ਵਹਾਅ। ਪੁਲੀਆਂ ਅਤੇ ਅੰਡਰਪਾਸ ਪਾਣੀ ਵਿੱਚ ਡੁੱਬੇ। ਟਰੈਫਿਕ ਡਾਇਵਰਟ।'
            : language === 'hi'
            ? 'शिवालिक पहाड़ियों से तेज पानी का बहाव। पुलिया व अंडरपास जलमग्न। भारी वाहनों का आवागमन बंद।'
            : 'Torrential runoff gushing from foothill catchments. Low-lying underpasses and bridges inundated; traffic diverted.';
      } else if (node.threatLevel === 'MEDIUM') {
        sceneBadge = language === 'pa' ? '👁️ ਨਿਗਰਾਨੀ ਦ੍ਰਿਸ਼' : language === 'hi' ? '👁️ निगरानी दृश्य' : '👁️ DRAINAGE WATCH SCENE';
        sceneBadgeBg = '#ca8a04';
        groundScene =
          language === 'pa'
            ? 'ਖੇਤੀਬਾੜੀ ਖੇਤਾਂ ਅਤੇ ਨਾਲੀਆਂ ਵਿੱਚ ਪਾਣੀ ਦਾ ਪੱਧਰ ਉੱਚਾ। ਸਲੂਇਸ ਗੇਟਾਂ ਰਾਹੀਂ ਪਾਣੀ ਦਾ ਨਿਕਾਸ ਜਾਰੀ।'
            : language === 'hi'
            ? 'खेतों और जल निकासी नालों में उच्च जलस्तर। स्लुइस गेट खोलकर जल निकासी की जा रही है।'
            : 'High agricultural drainage saturation. Regulator gates open to absorb flood runoff into buffer depressions.';
      } else {
        sceneBadge = language === 'pa' ? '🛡️ ਸੁਰੱਖਿਅਤ ਰਾਹਤ ਸ਼ੈਲਟਰ' : language === 'hi' ? '🛡️ सुरक्षित राहत शिविर' : '🛡️ SAFE RELIEF SHELTER';
        sceneBadgeBg = '#16a34a';
        groundScene =
          language === 'pa'
            ? 'ਉੱਚੇ ਸਥਾਨ \'ਤੇ ਸੁਰੱਖਿਅਤ ਰਾਹਤ ਕੈਂਪ। ਡਾਕਟਰੀ ਟੀਮ, ਪੀਣ ਵਾਲਾ ਸਾਫ਼ ਪਾਣੀ, ਸੁੱਕਾ ਰਾਸ਼ਨ ਅਤੇ ਬਿਸਤਰੇ ਤਿਆਰ।'
            : language === 'hi'
            ? 'ऊंचे स्थान पर सुरक्षित राहत केंद्र। चिकित्सा दल, स्वच्छ पेयजल, सूखा राशन व बिस्तर उपलब्ध।'
            : 'Designated high-elevation relief shelter fully operational with medical triage, potable drinking water, dry rations, and bed capacity.';
      }

      const popupHtml = `
        <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 240px; padding: 2px; line-height: 1.4;">
          <div style="margin-bottom: 5px; padding-bottom: 4px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
            <span style="background: ${sceneBadgeBg}; color: white; font-weight: 700; font-size: 9.5px; padding: 2px 6px; border-radius: 4px;">
              ${sceneBadge}
            </span>
            <span style="font-size: 11px; font-weight: 600; color: #64748b;">${districtName}</span>
          </div>

          <strong style="color: #0f172a; font-size: 12.5px; display: block; margin-bottom: 4px;">
            ${nodeName}
          </strong>

          <div style="background: #f8fafc; border-left: 3px solid ${markerColor}; padding: 5px 7px; margin-bottom: 6px; border-radius: 4px; font-size: 11px; color: #334155;">
            ${groundScene}
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px; margin-bottom: 6px; background: #ffffff; padding: 4px 6px; border: 1px solid #f1f5f9; border-radius: 6px;">
            <div><span style="color: #64748b;">${threatHeader}:</span> <b style="color: ${markerColor};">${threatLabel}</b></div>
            <div><span style="color: #64748b;">${gaugeHeader}:</span> <b>${node.waterLevelPct}%</b></div>
            <div><span style="color: #64748b;">${rainHeader}:</span> <b>${node.precipRate}</b></div>
            <div><span style="color: #64748b;">Status:</span> <b style="color: ${node.threatLevel === 'LOW' ? '#16a34a' : '#dc2626'};">${node.evacStatus}</b></div>
          </div>

          <div style="font-size: 11px; color: #475569; border-top: 1px dashed #e2e8f0; pt-1; margin-top: 4px;">
            <span style="font-weight: 600; color: #0f172a;">${directiveHeader}:</span> ${mitText}
          </div>
        </div>
      `;

      const marker = L.marker(node.coords, { icon: customIcon });
      marker.bindPopup(popupHtml);

      // Open popup on hover as requested
      marker.on('mouseover', function (this: L.Marker) {
        this.openPopup();
      });

      marker.addTo(layerGroupRef.current!);
    });
  }, [filteredNodes, language, t]);

  const handleResetMap = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([31.25, 75.6], 9);
    }
  };

  const handleExportData = () => {
    const headerRow =
      language === 'pa'
        ? 'ਨੋਡ ਨਾਮ,ਜ਼ਿਲ੍ਹਾ,ਖ਼ਤਰਾ ਪੱਧਰ,ਪਾਣੀ ਪੱਧਰ (%),ਵਰਖਾ ਦਰ,ਪ੍ਰਭਾਵਿਤ ਆਬਾਦੀ,ਨਿਕਾਸੀ ਸਥਿਤੀ,ਸਰਗਰਮ ਨਿਵਾਰਨ ਹਦਾਇਤ\n'
        : language === 'hi'
        ? 'नोड नाम,जिला,खतरा स्तर,जल स्तर (%),वर्षा दर,प्रभावित जनसंख्या,निकासी स्थिति,सक्रिय शमन निर्देश\n'
        : 'Node Name,District,Threat Level,Water Level (%),Precipitation Rate,Exposed Population,Evacuation Status,Mitigation Directive\n';

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      headerRow +
      RISK_NODES.map(
        (n) =>
          `"${t('node.name.' + n.id, n.name)}","${t('district.' + n.district, n.district)}","${t('common.' + n.threatLevel.toLowerCase(), n.threatLevel)}",${n.waterLevelPct},"${n.precipRate}","${n.population === 'Safe Zone' ? t('common.safeZone', 'Safe Zone') : n.population}","${t('common.' + n.evacStatus.toLowerCase(), n.evacStatus)}","${t('node.mit.' + n.id, n.mitigation)}"`
      ).join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `punjab_flood_telemetry_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* 1. Top Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 md:p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h2 className="text-lg md:text-xl font-bold text-slate-900">
              {t('map.bannerTitle', 'Punjab Geospatial Flood & Weather Risk Map')}
            </h2>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {t('map.bannerBadge', 'LIVE GIS TELEMETRY')}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-4xl">
            {t(
              'map.bannerDesc',
              'Multi-district hydrological surveillance covering Jalandhar (Doaba), Patiala (Ghaggar Basin), Hoshiarpur foothills, and Kapurthala riverine tracts. Hover or click markers to inspect ground scenes.'
            )}
          </p>
        </div>

        <button
          type="button"
          onClick={handleExportData}
          className="shrink-0 flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>{t('map.exportBtn', 'Export GIS Data')}</span>
        </button>
      </div>

      {/* 2. Visual Guide & Audio Bar */}
      <div className="bg-white text-slate-900 rounded-xl p-4 sm:p-5 border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-700 border border-blue-100 flex items-center justify-center shrink-0">
            <Layers className="w-5 h-5 text-blue-700" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900">
              {language === 'pa'
                ? 'ਨਕਸ਼ੇ ਉੱਤੇ ਰੰਗਾਂ ਦੇ ਦ੍ਰਿਸ਼ ਅਤੇ ਸਥਿਤੀ'
                : language === 'hi'
                ? 'मानचित्र पर रंगों के दृश्य व स्थिति'
                : 'Map Color Guide & Ground Scene Popups'}
            </h3>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-2 text-xs font-medium">
              <span className="flex items-center gap-1.5 bg-red-50 text-red-700 px-2.5 py-1 rounded border border-red-200">
                <span className="w-2 h-2 rounded-full bg-red-600" />
                <span>{language === 'pa' ? 'ਲਾਲ = ਪਾਣੀ ਭਰਿਆ / ਗੰਭੀਰ ਹੜ੍ਹ' : language === 'hi' ? 'लाल = जलभराव / गंभीर बाढ़' : 'Red = Critical Inundation Scene'}</span>
              </span>
              <span className="flex items-center gap-1.5 bg-amber-50 text-amber-800 px-2.5 py-1 rounded border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>{language === 'pa' ? 'ਪੀਲਾ/ਸੰਤਰੀ = ਚੋਅ ਵਹਾਅ / ਸਾਵਧਾਨੀ' : language === 'hi' ? 'पीला/नारंगी = चो बहाव / सावधानी' : 'Orange/Yellow = Choe Runoff Watch'}</span>
              </span>
              <span className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-600" />
                <span>{language === 'pa' ? 'ਹਰਾ = ਸੁਰੱਖਿਅਤ ਰਾਹਤ ਸ਼ੈਲਟਰ' : language === 'hi' ? 'हरा = सुरक्षित राहत शिविर' : 'Green = Operational Safe Camp'}</span>
              </span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSpeakMap}
          className={`shrink-0 px-3.5 py-2 rounded-lg font-semibold text-xs flex items-center gap-2 border transition-colors ${
            isSpeaking
              ? 'bg-amber-400 text-slate-950 border-amber-300'
              : 'bg-slate-900 hover:bg-slate-800 text-white border-slate-900'
          }`}
        >
          {isSpeaking ? (
            <>
              <VolumeX className="w-4 h-4 text-slate-950" />
              <span>{t('simple.voiceStop', 'Stop Audio')}</span>
            </>
          ) : (
            <>
              <Volume2 className="w-4 h-4 text-slate-300" />
              <span>{language === 'pa' ? 'ਨਕਸ਼ੇ ਬਾਰੇ ਸੁਣੋ' : language === 'hi' ? 'मानचित्र सुनें' : 'Listen Map Guide'}</span>
            </>
          )}
        </button>
      </div>

      {/* 3. Five Summary Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            {t('map.stat1.title', 'Critical Threat Nodes')}
          </span>
          <p className="text-xl sm:text-2xl font-bold text-red-600 font-mono mt-1">
            {t('map.stat1.val', '5 Nodes')}
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">{t('map.stat1.sub', 'Immediate SDRF deployment')}</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            {t('map.stat2.title', 'High Alert Sectors')}
          </span>
          <p className="text-xl sm:text-2xl font-bold text-amber-600 font-mono mt-1">
            {t('map.stat2.val', '4 Sectors')}
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">{t('map.stat2.sub', 'Canal / embankment vigil')}</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            {t('map.stat3.title', 'Watch & Standby')}
          </span>
          <p className="text-xl sm:text-2xl font-bold text-yellow-600 font-mono mt-1">
            {t('map.stat3.val', '4 Nodes')}
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">{t('map.stat3.sub', 'Root zone saturation >80%')}</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            {t('map.stat4.title', 'Designated Safe Havens')}
          </span>
          <p className="text-xl sm:text-2xl font-bold text-emerald-600 font-mono mt-1">
            {t('map.stat4.val', '8 High Grounds')}
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">{t('map.stat4.sub', 'Relief shelters operational')}</span>
        </div>

        <div className="col-span-2 sm:col-span-1 bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition-all duration-200 transform hover:scale-[1.03] hover:-translate-y-1 hover:shadow-lg cursor-pointer">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            {t('map.stat5.title', 'Est. Population at Risk')}
          </span>
          <p className="text-xl sm:text-2xl font-bold text-slate-900 font-mono mt-1">
            {t('map.stat5.val', '215,700')}
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">{t('map.stat5.sub', 'Across 4 river corridors')}</span>
        </div>
      </div>

      {/* 3. Interactive Leaflet Map Container */}
      <div className={`bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm transition-all relative isolate ${isExpanded ? 'fixed inset-4 z-[999] flex flex-col' : 'z-0'}`}>
        <div className="px-5 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-red-600" />
            <span className="text-sm font-bold text-slate-900">
              {t('map.mapSectionTitle', 'Punjab Severe Weather & Flood Risk Map')}
            </span>
            <span className="hidden sm:inline text-xs text-blue-600 font-mono font-semibold">
              [Google Maps • Live]
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Google Maps Layer Type Switcher */}
            <div className="flex items-center bg-white border border-slate-200 rounded-lg p-0.5 text-xs font-medium">
              <button
                type="button"
                onClick={() => setMapType('terrain')}
                className={`px-2 py-1 rounded transition-all cursor-pointer ${
                  mapType === 'terrain' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {language === 'pa' ? 'ਭੌਤਿਕ (Physical)' : language === 'hi' ? 'भौतिक (Physical)' : 'Physical'}
              </button>
              <button
                type="button"
                onClick={() => setMapType('streets')}
                className={`px-2 py-1 rounded transition-all cursor-pointer ${
                  mapType === 'streets' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {language === 'pa' ? 'ਸੜਕਾਂ (Streets)' : language === 'hi' ? 'सड़कें (Streets)' : 'Streets'}
              </button>
              <button
                type="button"
                onClick={() => setMapType('hybrid')}
                className={`px-2 py-1 rounded transition-all cursor-pointer ${
                  mapType === 'hybrid' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {language === 'pa' ? 'ਸੈਟੇਲਾਈਟ' : language === 'hi' ? 'सैटेलाइट' : 'Satellite'}
              </button>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center bg-white border border-slate-200 rounded-lg p-0.5 text-xs font-medium">
              <button
                type="button"
                onClick={() => setFilter('ALL')}
                className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                  filter === 'ALL' ? 'bg-slate-900 text-white font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {t('map.filter.all', 'All (21)')}
              </button>
              <button
                type="button"
                onClick={() => setFilter('CRITICAL')}
                className={`px-2 py-1 rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                  filter === 'CRITICAL' ? 'bg-red-600 text-white font-semibold' : 'text-red-600 hover:bg-red-50'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                {t('map.filter.critical', 'Critical')}
              </button>
              <button
                type="button"
                onClick={() => setFilter('HIGH')}
                className={`px-2 py-1 rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                  filter === 'HIGH' ? 'bg-amber-600 text-white font-semibold' : 'text-amber-600 hover:bg-amber-50'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                {t('map.filter.high', 'High')}
              </button>
              <button
                type="button"
                onClick={() => setFilter('MEDIUM')}
                className={`px-2 py-1 rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                  filter === 'MEDIUM' ? 'bg-yellow-600 text-white font-semibold' : 'text-yellow-600 hover:bg-yellow-50'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                {t('map.filter.mod', 'Mod')}
              </button>
              <button
                type="button"
                onClick={() => setFilter('LOW')}
                className={`px-2 py-1 rounded-md flex items-center gap-1 transition-all cursor-pointer ${
                  filter === 'LOW' ? 'bg-emerald-600 text-white font-semibold' : 'text-emerald-600 hover:bg-emerald-50'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                {t('map.filter.safe', 'Safe')}
              </button>
            </div>

            <button
              type="button"
              onClick={handleResetMap}
              title={t('map.reset', 'Reset Zoom')}
              className="p-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t('map.reset', 'Reset')}</span>
            </button>

            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              title={t('map.expand', 'Toggle Fullscreen')}
              className="p-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs cursor-pointer"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Map Leaflet Canvas with Click-to-Zoom Protection */}
        <div className="relative w-full overflow-hidden">
          <div
            ref={mapContainerRef}
            onClick={() => {
              setIsZoomActive(true);
              mapInstanceRef.current?.scrollWheelZoom.enable();
            }}
            className={`w-full bg-slate-100 relative ${isExpanded ? 'flex-1' : 'h-[440px]'}`}
            style={{ minHeight: '380px' }}
          />

          {/* Floating Click-to-Zoom Indicator / Controller */}
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] pointer-events-auto select-none">
            {!isZoomActive ? (
              <button
                type="button"
                onClick={() => {
                  setIsZoomActive(true);
                  mapInstanceRef.current?.scrollWheelZoom.enable();
                }}
                className="px-3 py-1.5 rounded-full bg-white/95 hover:bg-white shadow-md border border-slate-300 text-xs font-semibold text-slate-800 flex items-center gap-1.5 cursor-pointer backdrop-blur-xs transition-all hover:scale-105"
                title="Click to enable scroll wheel zoom on map"
              >
                <span>🖱️</span>
                <span>
                  {language === 'pa'
                    ? 'ਜ਼ੂਮ ਕਰਨ ਲਈ ਨਕਸ਼ੇ ਤੇ ਕਲਿੱਕ ਕਰੋ'
                    : language === 'hi'
                    ? 'ज़ूम करने हेतु मानचित्र पर क्लिक करें'
                    : 'Click map to enable scroll zoom'}
                </span>
              </button>
            ) : (
              <div className="px-3 py-1.5 rounded-full bg-blue-600/95 shadow-md border border-blue-400 text-xs font-semibold text-white flex items-center gap-1.5 backdrop-blur-xs animate-in fade-in">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>
                  {language === 'pa'
                    ? 'ਸਕ੍ਰੌਲ ਜ਼ੂਮ ਚਾਲੂ • ਪੇਜ ਸਕ੍ਰੌਲ ਲਈ ਕਰਸਰ ਬਾਹਰ ਕਰੋ'
                    : language === 'hi'
                    ? 'स्क्रॉल ज़ूम सक्रिय • पेज स्क्रॉल हेतु कर्सर बाहर ले जाएं'
                    : 'Scroll zoom active • Move cursor away to scroll page'}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Complete 16-Row Telemetry Nodes Table (Screenshot 4) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              {t('map.matrixTitle', 'Geospatial Telemetry & Risk Mitigation Matrix')}
            </h3>
            <p className="text-xs text-slate-500">
              {t('map.matrixSubtitle', 'Live multi-district gauge nodes and civil defence status')}
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {t('map.showingNodes', `Showing ${filteredNodes.length} of 16 Nodes`)
              .replace('{count}', String(filteredNodes.length))
              .replace('{total}', '16')}
          </span>
        </div>

        <div className="overflow-x-auto -mx-6 px-6">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-mono text-[11px]">
                <th className="py-2.5 pr-4 font-normal">{t('map.table.node', 'Hydrological Node')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.district', 'District')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.threat', 'Threat')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.capacity', 'Gauge Cap.')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.rain', 'Precip Rate')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.pop', 'Exposed Pop.')}</th>
                <th className="py-2.5 px-3 font-normal">{t('map.table.evac', 'Status')}</th>
                <th className="py-2.5 pl-3 font-normal min-w-[280px]">{t('map.table.mitigation', 'Active Mitigation Directive')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredNodes.map((node) => {
                const isOverCap = node.waterLevelPct >= 100;
                return (
                  <tr key={node.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 pr-4 font-medium text-slate-900 whitespace-nowrap">
                      {t('node.name.' + node.id, node.name)}
                    </td>
                    <td className="py-3.5 px-3 text-slate-600 whitespace-nowrap">
                      {t('district.' + node.district, node.district)}
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          node.threatLevel === 'CRITICAL'
                            ? 'bg-red-100 text-red-700'
                            : node.threatLevel === 'HIGH'
                            ? 'bg-amber-100 text-amber-800'
                            : node.threatLevel === 'MEDIUM'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {t('common.' + node.threatLevel.toLowerCase(), node.threatLevel)}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              isOverCap ? 'bg-red-600' : node.waterLevelPct > 75 ? 'bg-amber-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(node.waterLevelPct, 100)}%` }}
                          />
                        </div>
                        <span className={`font-mono text-xs font-semibold ${isOverCap ? 'text-red-600' : 'text-slate-700'}`}>
                          {node.waterLevelPct}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-3 font-mono text-slate-700 whitespace-nowrap">{node.precipRate}</td>
                    <td className="py-3.5 px-3 font-mono text-slate-800 whitespace-nowrap">
                      {node.population === 'Safe Zone' ? t('common.safeZone', 'Safe Zone') : node.population}
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          node.evacStatus === 'MANDATORY'
                            ? 'bg-red-600 text-white'
                            : node.evacStatus === 'ADVISORY'
                            ? 'bg-amber-500 text-white'
                            : node.evacStatus === 'STANDBY'
                            ? 'bg-slate-200 text-slate-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {t('common.' + node.evacStatus.toLowerCase(), node.evacStatus)}
                      </span>
                    </td>
                    <td className="py-3.5 pl-3 text-slate-600 leading-relaxed">
                      {t('node.mit.' + node.id, node.mitigation)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
