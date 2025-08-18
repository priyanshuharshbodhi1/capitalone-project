import React, { useState, useRef, useCallback } from 'react';
import { Camera, Upload, MapPin, Loader2, Leaf, AlertTriangle, CheckCircle, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useLanguage } from '../../context/LanguageContext';
import { useTranslation } from 'react-i18next';

interface LocationData {
  latitude: number;
  longitude: number;
  placeName?: string;
  state?: string;
  address?: string;
}

interface DiagnosisResult {
  disease: string;
  confidence: number;
  symptoms: string[];
  treatment: string[];
  prevention: string[];
  severity: 'low' | 'medium' | 'high';
  localRemedies: string[];
  stage: string;
  affectedParts: string[];
  recommendedAction: string;
  diseaseExplanation: string;
  economicImpact: string;
  treatmentTiming: string;
  followUpCare: string;
}

const PlantDoc: React.FC = () => {
  const { currentLanguage } = useLanguage();
  const { t } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [plantName, setPlantName] = useState('');
  const [location, setLocation] = useState<LocationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [showValidationErrors, setShowValidationErrors] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = useCallback((file: File) => {
    if (file && file.type.startsWith("image/")) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target?.result as string);
      reader.readAsDataURL(file);
    } else {
      toast.error(t('plantdoc.errors.invalidImageFile'));
    }
  }, [t]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageSelect(file);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleImageSelect(file);
    },
    [handleImageSelect]
  );

  const getCurrentLocation = async () => {
    setIsGettingLocation(true);
    try {
      if (!navigator.geolocation) {
        throw new Error(t('plantdoc.errors.geolocationNotSupported'));
      }

      const position = await new Promise<GeolocationPosition>(
        (resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000,
          });
        }
      );

      const { latitude, longitude } = position.coords;

      // Reverse geocoding to get place name and state
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`
        );
        const data = await response.json();
        const placeName =
          data.address?.city ||
          data.address?.town ||
          data.address?.village ||
          t('plantdoc.location.unknownPlace');
        const state = data.address?.state || t('plantdoc.location.state');
        const address = data.display_name || t('plantdoc.location.locationFound');

        setLocation({ latitude, longitude, placeName, state, address });
        toast.success(t('plantdoc.location.capturedSuccess'));
      } catch {
        setLocation({
          latitude,
          longitude,
          placeName: t('plantdoc.location.unknownPlace'),
          state: t('plantdoc.location.unknownState'),
          address: t('plantdoc.location.locationFound'),
        });
        toast.success(t('plantdoc.location.capturedSuccess'));
      }
    } catch {
      toast.error(
        t('plantdoc.errors.locationAccess')
      );
    } finally {
      setIsGettingLocation(false);
    }
  };

  const diagnosePlant = async () => {
    // Show validation errors when user tries to submit
    setShowValidationErrors(true);

    // Validation with red border feedback
    let hasErrors = false;

    if (!selectedImage) {
      toast.error(t('plantdoc.validation.selectImage'));
      hasErrors = true;
    }

    if (!plantName.trim()) {
      toast.error(t('plantdoc.validation.enterPlantName'));
      hasErrors = true;
    }

    if (!location) {
      toast.error(t('plantdoc.validation.captureLocation'));
      hasErrors = true;
    }

    if (hasErrors) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", selectedImage);
      formData.append("description", description);
      formData.append("plantName", plantName);
      formData.append("language", currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1));
      if (location) {
        formData.append("latitude", location.latitude.toString());
        formData.append("longitude", location.longitude.toString());
        if (location.placeName)
          formData.append("placeName", location.placeName);
        if (location.state) formData.append("state", location.state);
      }

      const response = await fetch("/api/diagnose-plant", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(t('plantdoc.errors.diagnosisFailed'));

      const result = await response.json();
      setDiagnosis(result);

      // Clear form after successful diagnosis
      setSelectedImage(null);
      setImagePreview(null);
      setPlantName("");
      setDescription("");
      setLocation(null);

      toast.success(t('plantdoc.success.completed'));
    } catch (error) {
      toast.error(t('plantdoc.errors.diagnosisFailedTryAgain'));
      console.error("Diagnosis error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearAll = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setDescription("");
    setPlantName("");
    setLocation(null);
    setDiagnosis(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "low":
        return "text-green-600 bg-green-50 border-green-200";
      case "medium":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "high":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "low":
        return <CheckCircle className="h-4 w-4" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4" />;
      case "high":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Leaf className="h-4 w-4" />;
    }
  };

  const isValidPlantDiagnosis = (diagnosis: DiagnosisResult) => {
    const invalidDiseases = [
      'Invalid Image - Not a Plant',
      'Plant Name Mismatch', 
      'Analysis Error',
      'Analysis Failed'
    ];
    return !invalidDiseases.includes(diagnosis.disease);
  };

  const isHealthyPlant = (diagnosis: DiagnosisResult) => {
    return diagnosis.disease === 'Healthy Plant';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-3 sm:p-4 lg:p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-emerald-100 p-3 rounded-full">
              <Leaf className="h-8 w-8 text-emerald-600" />
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            {t('plantdoc.title')}
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            {t('plantdoc.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Left Column - Upload */}
          <div className="space-y-6">
            {/* Image Upload */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {t('plantdoc.uploadTitle')}
              </h3>

              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center hover:border-emerald-400 transition-colors cursor-pointer ${
                  showValidationErrors && !selectedImage
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/*"
                  className="hidden"
                />

                {imagePreview ? (
                  <div className="relative">
                    <img
                      src={imagePreview}
                      alt={t('plantdoc.previewAlt')}
                      className="max-h-64 mx-auto rounded-lg shadow-sm"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedImage(null);
                        setImagePreview(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = "";
                        }
                      }}
                      className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 transition-colors shadow-lg"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex justify-center space-x-4">
                      <Camera className="h-8 w-8 text-gray-400" />
                      <Upload className="h-8 w-8 text-gray-400" />
                    </div>
                    <p className="text-gray-600">
                      {t('plantdoc.uploadHint')}
                    </p>
                    <p className="text-xs text-gray-500">
                      {t('plantdoc.uploadTypes')}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Input Details */}
          <div className="space-y-6">
            {/* Plant Name */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {t('plantdoc.plantNameTitle')}
              </h3>
              <input
                type="text"
                value={plantName}
                onChange={(e) => setPlantName(e.target.value)}
                placeholder={t('plantdoc.plantNamePlaceholder')}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm ${
                  showValidationErrors && !plantName.trim()
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
              />
            </div>

            {/* Additional Details */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {t('plantdoc.detailsTitle')}
              </h3>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t('plantdoc.detailsPlaceholder')}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none text-sm"
              />
            </div>

            {/* Location */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {t('plantdoc.location.title')}
              </h3>
              {location ? (
                <div className="flex items-start space-x-3 p-3 bg-emerald-50 rounded-lg">
                  <MapPin className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-emerald-900">
                      {t('plantdoc.location.captured')}
                    </p>
                    <p className="text-xs text-emerald-700">
                      {location.placeName}, {location.state}
                    </p>
                    <p className="text-xs text-emerald-600">
                      {location.latitude.toFixed(4)},{" "}
                      {location.longitude.toFixed(4)}
                    </p>
                  </div>
                </div>
              ) : (
                <button
                  onClick={getCurrentLocation}
                  disabled={isGettingLocation}
                  className={`flex items-center space-x-2 w-full p-3 border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 ${
                    showValidationErrors && !location
                      ? "border-red-300"
                      : "border-gray-300"
                  }`}
                >
                  {isGettingLocation ? (
                    <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
                  ) : (
                    <MapPin className="h-5 w-5 text-gray-600" />
                  )}
                  <span className="text-sm text-gray-700">
                    {isGettingLocation
                      ? t('plantdoc.location.getting')
                      : t('plantdoc.location.getCurrent')}
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons - End of Form */}
        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button
            onClick={diagnosePlant}
            disabled={isLoading || !selectedImage || !plantName.trim()}
            className="flex-1 bg-emerald-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>{t('plantdoc.analyzing')}</span>
              </>
            ) : (
              <>
                <Leaf className="h-5 w-5" />
                <span>{t('plantdoc.diagnose')}</span>
              </>
            )}
          </button>
          <button
            onClick={clearAll}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            {t('plantdoc.clearAll')}
          </button>
        </div>

        {/* Results Section - Full Width */}
        {diagnosis && (
          <div className="mt-8">
            {/* Error State for Invalid Images */}
            {!isValidPlantDiagnosis(diagnosis) && (
              <div className="bg-white rounded-xl shadow-sm border border-red-200 p-4 sm:p-6">
                <div className="flex items-center space-x-3 text-red-600">
                  <X className="h-6 w-6" />
                  <div>
                    <h3 className="text-lg font-semibold">{t('plantdoc.errors.unableToProcess')}</h3>
                    <p className="text-sm text-red-500 mt-1">
                      {diagnosis.disease === 'Invalid Image - Not a Plant' && t('plantdoc.errors.invalidImageNotPlant')}
                      {diagnosis.disease === 'Plant Name Mismatch' && t('plantdoc.errors.nameMismatch')}
                      {(diagnosis.disease === 'Analysis Error' || diagnosis.disease === 'Analysis Failed') && t('plantdoc.errors.technicalError')}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Healthy Plant State */}
            {isHealthyPlant(diagnosis) && (
              <div className="bg-white rounded-xl shadow-sm border border-green-200 p-4 sm:p-6">
                <div className="flex items-center space-x-3 text-green-600">
                  <CheckCircle className="h-6 w-6" />
                  <div>
                    <h3 className="text-lg font-semibold">{t('plantdoc.healthy.title')}</h3>
                    <p className="text-sm text-green-600 mt-1">
                      {t('plantdoc.healthy.message')}
                    </p>
                  </div>
                </div>
                {diagnosis.prevention.length > 0 && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">{t('plantdoc.healthy.keepHealthy')}</h4>
                    <ul className="space-y-1 text-sm text-green-700">
                      {diagnosis.prevention.map((tip, idx) => (
                        <li key={idx}>• {tip}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Full Diagnosis for Valid Disease Cases */}
            {isValidPlantDiagnosis(diagnosis) && !isHealthyPlant(diagnosis) && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">{t('plantdoc.results.title')}</h3>
                
                {/* Disease Info Header */}
                <div className="space-y-6">
                  <div className="bg-gradient-to-r from-emerald-50 to-green-50 p-4 rounded-lg border border-emerald-200">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-lg font-semibold text-gray-900">{t('plantdoc.results.identifiedDisease')}</h4>
                      <div className={`flex items-center space-x-1 px-3 py-1 rounded-full border text-sm font-medium ${getSeverityColor(diagnosis.severity)}`}>
                        {getSeverityIcon(diagnosis.severity)}
                        <span className="capitalize">{diagnosis.severity} {t('plantdoc.results.severity')}</span>
                      </div>
                    </div>
                    <p className="text-xl font-bold text-emerald-700 mb-2">{diagnosis.disease}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>{t('plantdoc.results.confidence')}: {Math.round(diagnosis.confidence * 100)}%</span>
                      {diagnosis.stage && <span>{t('plantdoc.results.stage')}: {diagnosis.stage}</span>}
                      {diagnosis.affectedParts.length > 0 && (
                        <span>{t('plantdoc.results.affected')}: {diagnosis.affectedParts.join(', ')}</span>
                      )}
                    </div>
                  </div>

                  {/* Disease Explanation */}
                  {diagnosis.diseaseExplanation && (
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                        <Leaf className="h-4 w-4 mr-2 text-blue-600" />
                        {t('plantdoc.results.understanding')}
                      </h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{diagnosis.diseaseExplanation}</p>
                    </div>
                  )}

                  {/* Economic Impact */}
                  {diagnosis.economicImpact && (
                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                        <AlertTriangle className="h-4 w-4 mr-2 text-amber-600" />
                        {t('plantdoc.results.economicImpact')}
                      </h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{diagnosis.economicImpact}</p>
                    </div>
                  )}

                  {/* Immediate Action */}
                  {diagnosis.recommendedAction && (
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                        <CheckCircle className="h-4 w-4 mr-2 text-red-600" />
                        {t('plantdoc.results.immediateAction')}
                      </h4>
                      <p className="text-sm text-gray-700 leading-relaxed font-medium">{diagnosis.recommendedAction}</p>
                    </div>
                  )}

                  {/* Symptoms */}
                  {diagnosis.symptoms.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">{t('plantdoc.results.symptoms')}</h4>
                      <div className="space-y-2">
                        {diagnosis.symptoms.map((symptom, idx) => (
                          <div key={idx} className="bg-gray-50 p-3 rounded-lg border">
                            <p className="text-sm text-gray-700">{symptom}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Treatment */}
                  {diagnosis.treatment.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">{t('plantdoc.results.treatment')}</h4>
                      <div className="space-y-3">
                        {diagnosis.treatment.map((treatment, idx) => (
                          <div key={idx} className="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                            <p className="text-sm text-gray-700 leading-relaxed">{treatment}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Treatment Timing */}
                  {diagnosis.treatmentTiming && (
                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                      <h4 className="font-semibold text-gray-900 mb-2">{t('plantdoc.results.treatmentTiming')}</h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{diagnosis.treatmentTiming}</p>
                    </div>
                  )}

                  {/* Local Remedies */}
                  {diagnosis.localRemedies.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">{t('plantdoc.results.localRemedies')}</h4>
                      <div className="space-y-3">
                        {diagnosis.localRemedies.map((remedy, idx) => (
                          <div key={idx} className="bg-green-50 p-3 rounded-lg border border-green-200">
                            <p className="text-sm text-gray-700 leading-relaxed">{remedy}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Prevention */}
                  {diagnosis.prevention.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">{t('plantdoc.results.prevention')}</h4>
                      <div className="space-y-3">
                        {diagnosis.prevention.map((tip, idx) => (
                          <div key={idx} className="bg-indigo-50 p-3 rounded-lg border border-indigo-200">
                            <p className="text-sm text-gray-700 leading-relaxed">{tip}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Follow-up Care */}
                  {diagnosis.followUpCare && (
                    <div className="bg-teal-50 p-4 rounded-lg border border-teal-200">
                      <h4 className="font-semibold text-gray-900 mb-2">{t('plantdoc.results.followUp')}</h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{diagnosis.followUpCare}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlantDoc;
