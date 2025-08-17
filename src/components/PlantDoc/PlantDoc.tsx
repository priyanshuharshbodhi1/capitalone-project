import React, { useState, useRef, useCallback } from 'react';
import { Camera, Upload, MapPin, Loader2, Leaf, AlertTriangle, CheckCircle, X } from 'lucide-react';
import toast from 'react-hot-toast';

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
}

const PlantDoc: React.FC = () => {
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
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target?.result as string);
      reader.readAsDataURL(file);
    } else {
      toast.error('Please select a valid image file');
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageSelect(file);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleImageSelect(file);
  }, [handleImageSelect]);

  const getCurrentLocation = async () => {
    setIsGettingLocation(true);
    try {
      if (!navigator.geolocation) {
        throw new Error('Geolocation not supported');
      }

      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000,
        });
      });

      const { latitude, longitude } = position.coords;
      
      // Reverse geocoding to get place name and state
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`
        );
        const data = await response.json();
        const placeName = data.address?.city || data.address?.town || data.address?.village || 'Unknown Place';
        const state = data.address?.state || 'State';
        const address = data.display_name || 'Location found';
        
        setLocation({ latitude, longitude, placeName, state, address });
        toast.success('Location captured successfully');
      } catch {
        setLocation({ latitude, longitude, placeName: 'Unknown Place', state: 'Unknown State', address: 'Location found' });
        toast.success('Location captured successfully');
      }
    } catch {
      toast.error('Unable to get location. Please ensure location access is enabled.');
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
      toast.error('Please select an image first');
      hasErrors = true;
    }
    
    if (!plantName.trim()) {
      toast.error('Please enter the plant name');
      hasErrors = true;
    }
    
    if (!location) {
      toast.error('Please capture your location first');
      hasErrors = true;
    }
    
    if (hasErrors) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('description', description);
      formData.append('plantName', plantName);
      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
        if (location.placeName) formData.append('placeName', location.placeName);
        if (location.state) formData.append('state', location.state);
      }

      const response = await fetch('/api/diagnose-plant', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Diagnosis failed');

      const result = await response.json();
      setDiagnosis(result);
      
      // Clear form after successful diagnosis
      setSelectedImage(null);
      setImagePreview(null);
      setPlantName('');
      setDescription('');
      setLocation(null);
      
      toast.success('Diagnosis completed successfully!');
    } catch (error) {
      toast.error('Diagnosis failed. Please try again.');
      console.error('Diagnosis error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearAll = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setDescription('');
    setPlantName('');
    setLocation(null);
    setDiagnosis(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low': return <CheckCircle className="h-4 w-4" />;
      case 'medium': return <AlertTriangle className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      default: return <Leaf className="h-4 w-4" />;
    }
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
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">PlantDoc</h1>
          <p className="text-sm sm:text-base text-gray-600">
            AI-Powered Crop Disease Diagnosis & Treatment Recommendations
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Left Column - Upload */}
          <div className="space-y-6">
            {/* Image Upload */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Plant Image</h3>
              
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center hover:border-emerald-400 transition-colors cursor-pointer ${
                  showValidationErrors && !selectedImage ? 'border-red-300' : 'border-gray-300'
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
                      alt="Plant preview" 
                      className="max-h-64 mx-auto rounded-lg shadow-sm"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleFileChange(e);
                      }}
                      className={`w-full h-64 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-emerald-400 hover:bg-emerald-50 transition-colors ${
                        !selectedImage ? 'border-red-300' : 'border-gray-300'
                      }`}                    >
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
                      Click to upload or drag and drop a plant image
                    </p>
                    <p className="text-xs text-gray-500">
                      PNG, JPG, JPEG up to 10MB
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
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Plant Name</h3>
              <input
                type="text"
                value={plantName}
                onChange={(e) => setPlantName(e.target.value)}
                placeholder="Enter the plant name (e.g., Tomato, Wheat, Rice...)"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm ${
                  showValidationErrors && !plantName.trim() ? 'border-red-300' : 'border-gray-300'
                }`}
              />
            </div>

            {/* Additional Details */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Details</h3>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe any symptoms you've noticed, when they started, or any treatments you've tried..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none text-sm"
              />
            </div>

            {/* Location */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Location</h3>
              {location ? (
                <div className="flex items-start space-x-3 p-3 bg-emerald-50 rounded-lg">
                  <MapPin className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-emerald-900">Location captured</p>
                    <p className="text-xs text-emerald-700">{location.placeName}, {location.state}</p>
                    <p className="text-xs text-emerald-600">
                      {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                    </p>
                  </div>
                </div>
              ) : (
                <button
                  onClick={getCurrentLocation}
                  disabled={isGettingLocation}
                  className={`flex items-center space-x-2 w-full p-3 border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 ${
                    showValidationErrors && !location ? 'border-red-300' : 'border-gray-300'
                  }`}
                >
                  {isGettingLocation ? (
                    <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
                  ) : (
                    <MapPin className="h-5 w-5 text-gray-600" />
                  )}
                  <span className="text-sm text-gray-700">
                    {isGettingLocation ? 'Getting location...' : 'Get current location'}
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
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Leaf className="h-5 w-5" />
                <span>Diagnose Plant</span>
              </>
            )}
          </button>
          <button
            onClick={clearAll}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Clear All
          </button>
        </div>

        {/* Results Section - Full Width */}
        {diagnosis && (
          <div className="mt-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">Diagnosis Results</h3>
                
                {/* Disease Info */}
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">Identified Disease</h4>
                      <div className={`flex items-center space-x-1 px-2 py-1 rounded-full border text-xs font-medium ${getSeverityColor(diagnosis.severity)}`}>
                        {getSeverityIcon(diagnosis.severity)}
                        <span className="capitalize">{diagnosis.severity} Severity</span>
                      </div>
                    </div>
                    <p className="text-lg font-semibold text-emerald-700">{diagnosis.disease}</p>
                    <p className="text-sm text-gray-600">Confidence: {Math.round(diagnosis.confidence * 100)}%</p>
                  </div>

                  {diagnosis.symptoms.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Symptoms</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {diagnosis.symptoms.map((symptom, idx) => (
                          <li key={idx}>{symptom}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {diagnosis.treatment.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Treatment Recommendations</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {diagnosis.treatment.map((treatment, idx) => (
                          <li key={idx}>{treatment}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {diagnosis.localRemedies.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Local & Affordable Remedies</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {diagnosis.localRemedies.map((remedy, idx) => (
                          <li key={idx}>{remedy}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {diagnosis.prevention.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Prevention Tips</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {diagnosis.prevention.map((tip, idx) => (
                          <li key={idx}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
      </div>
    </div>
  );
};

export default PlantDoc;
