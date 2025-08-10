import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft, 
  User, 
  Mail, 
  Phone, 
  Building, 
  MapPin, 
  Globe, 
  Star, 
  Edit, 
  Trash2, 
  Plus,
  Calendar,
  ExternalLink
} from "lucide-react";
import { leadApi } from "@/lib/api";
import type { Lead } from "@/lib/api";

const LeadDetails = () => {
  const { leadId } = useParams();
  const [lead, setLead] = useState<Lead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLead = async () => {
      if (!leadId) return;
      try {
        const leadData = await leadApi.getLead(parseInt(leadId));
        setLead(leadData as Lead);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching lead:', error);
        setIsLoading(false);
      }
    };

    fetchLead();
  }, [leadId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "new": return "bg-blue-50 text-blue-700 border-blue-200";
      case "contacted": return "bg-green-50 text-green-700 border-green-200";
      case "qualified": return "bg-purple-50 text-purple-700 border-purple-200";
      case "converted": return "bg-emerald-50 text-emerald-700 border-emerald-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-50 text-red-700 border-red-200";
      case "medium": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "low": return "bg-gray-50 text-gray-700 border-gray-200";
      case "urgent": return "bg-red-100 text-red-800 border-red-300";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen  p-4 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="min-h-screen  p-4 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <p>Lead not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen  p-4 lg:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <Link to="/leads">
            <Button variant="outline" size="sm" className="border-black text-black hover:bg-gray-50">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Leads
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl lg:text-3xl font-bold text-black">{lead.full_name}</h1>
            <p className="text-gray-600 mt-1">{lead.job_title} at {lead.company}</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <Button variant="outline" className="border-black text-black hover:bg-gray-50">
              <Edit className="w-4 h-4 mr-2" />
              Edit Lead
            </Button>
            <Button variant="outline" className="border-red-300 text-red-700 hover:bg-red-50">
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>

        {/* Lead Profile Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card className="border-black ">
              <CardHeader>
                <CardTitle className="text-black flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Lead Information
                </CardTitle>
                <CardDescription>Contact details and professional information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Contact Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <Mail className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <a 
                          href={`mailto:${lead.email}`}
                          className="font-medium text-black hover:text-blue-600"
                        >
                          {lead.email}
                        </a>
                        
                        <Badge className="ml-2 bg-green-50 text-green-700 border-green-200">Valid</Badge>
                        
                      </div>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <Phone className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">Phone</p>
                        <a 
                          href={`tel:${lead.phone}`}
                          className="font-medium text-black hover:text-blue-600"
                        >
                          {lead.phone}
                        </a>
                        <Badge className="ml-2 bg-green-50 text-green-700 border-green-200">Valid</Badge>
                        
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Building className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">Company & Role</p>
                        <p className="font-medium text-black">{lead.company}</p>
                        <p className="text-sm text-gray-600">{lead.job_title}</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <MapPin className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">Location</p>
                        <p className="font-medium text-black">{lead.city}, {lead.country}</p>
                        <p className="text-sm text-gray-600">{lead.industry}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Globe className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">LinkedIn</p>
                        <a 
                          href={lead.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-black hover:text-blue-600 flex items-center"
                        >
                          View Profile
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                      </div>
                    </div>

                    {/* <div className="flex items-start gap-3">
                      <Star className="w-5 h-5 text-gray-600 mt-0.5" />
                      <div>
                        <p className="text-sm text-gray-600">Lead Score</p>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-black">{lead.lead_score}</span>
                          <span className="text-sm text-gray-600">/ 100</span>
                        </div>
                      </div>
                    </div> */}
                  </div>
                </div>

                <Separator className="bg-gray-200" />

                {/* Tags */}
                <div>
                  <p className="text-sm text-gray-600 mb-3">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {lead.tags.split(',').map((tag, index) => (
                      <Badge 
                        key={index} 
                        className="bg-gray-100 text-gray-700 border-gray-300"
                      >
                        {tag.trim()}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                {/* <div>
                  <p className="text-sm text-gray-600 mb-2">Data Completeness</p>
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-black">Score:</span>
                      <span className="font-medium text-black">{lead.data_completeness_score}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-black">Social Profiles:</span>
                      <span className="font-medium text-black">{lead.social_profiles_count}</span>
                    </div>
                  </div>
                </div> */}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status & Priority */}
            <Card className="border-black ">
              <CardHeader>
                <CardTitle className="text-black text-lg">Status & Priority</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* <div>
                  <p className="text-sm text-gray-600 mb-2">Status</p>
                  <Badge className={getStatusColor(lead.lead_status)}>
                    {lead.lead_status.charAt(0).toUpperCase() + lead.lead_status.slice(1)}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-2">Priority</p>
                  <Badge className={getPriorityColor(lead.priority)}>
                    {lead.priority.charAt(0).toUpperCase() + lead.priority.slice(1)}
                  </Badge>
                </div> */}
                <Separator className="bg-gray-200" />
                <div>
                  <p className="text-sm text-gray-600 mb-1">Created</p>
                  <p className="text-black font-medium">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Source Information */}
            <Card className="border-black ">
              <CardHeader>
                <CardTitle className="text-black text-lg">Source Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Source File</p>
                  <p className="text-black font-medium">{lead.source_file_name}</p>
                  <p className="text-sm text-gray-600">Row {lead.source_file_row}</p>
                </div>
                <Separator className="bg-gray-200" />
                <div>
                  <p className="text-sm text-gray-600 mb-1">Last Updated</p>
                  <p className="text-black font-medium">
                    {new Date(lead.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadDetails;
