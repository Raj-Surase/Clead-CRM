// import { useState, useEffect } from "react";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Textarea } from "@/components/ui/textarea";
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
// import { Checkbox } from "@/components/ui/checkbox";
// import { Label } from "@/components/ui/label";
// import { Plus, ArrowLeft, Calendar, Clock, User, AlertTriangle, Loader2, Search, X } from "lucide-react";
// import { Link, useNavigate, useLocation, useSearchParams } from "react-router-dom";
// import { calendarApi } from "@/lib/calendarApi";
// import { leadApi } from "@/lib/leadApi";
// import { toast } from "sonner";
// import { Event, Lead } from "@/lib/api";
// import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";
// import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

// const CreateEvent = () => {
//   const navigate = useNavigate();
//   const location = useLocation();
//   const [searchParams] = useSearchParams();
//   const [isLoading, setIsLoading] = useState(false);
//   const [leads, setLeads] = useState<any[]>([]);
//   const [searchTerm, setSearchTerm] = useState("");
//   const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
//   const [showLeadResults, setShowLeadResults] = useState(false);

//   // Utility to convert UTC ISO string to local datetime-local input value
//   const toLocalDateTimeInputValue = (isoString: string) => {
//     if (!isoString) return "";
//     const date = new Date(isoString);
//     // Get local time in YYYY-MM-DDTHH:mm format
//     const pad = (n: number) => n.toString().padStart(2, '0');
//     return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
//   };

//   // Get and format start and end times from query parameters or state
//   const startFromQuery = toLocalDateTimeInputValue(searchParams.get('start') || location.state?.eventDetails?.start_datetime || "");
//   const endFromQuery = toLocalDateTimeInputValue(searchParams.get('end') || location.state?.eventDetails?.end_datetime || "");

//   // Initialize formData with default values, location.state, or query parameters
//   const [formData, setFormData] = useState({
//     // Required fields
//     title: location.state?.eventDetails?.title || "",
//     start_datetime: startFromQuery || "",
//     end_datetime: endFromQuery || "",
//     event_type: location.state?.eventDetails?.event_type || "",
    
//     // Optional fields with defaults
//     timezone: location.state?.eventDetails?.timezone || "UTC",
//     all_day: location.state?.eventDetails?.all_day || false,
//     priority: location.state?.eventDetails?.priority || "",
//     location: location.state?.eventDetails?.location || "",
//     meeting_url: location.state?.eventDetails?.meeting_url || "",
    
//     // Lead related fields
//     lead_id: location.state?.eventDetails?.lead_id || "",
//     lead_name: location.state?.eventDetails?.lead_name || "",
//     lead_email: location.state?.eventDetails?.lead_email || "",
//     lead_phone: location.state?.eventDetails?.lead_phone || "",
//     lead_company: location.state?.eventDetails?.lead_company || "",
    
//     // Additional optional fields
//     description: location.state?.eventDetails?.description || "",
//     notes: location.state?.eventDetails?.notes || "",
//     reminder_minutes: location.state?.eventDetails?.reminder_minutes || [15],
//     email_reminders: location.state?.eventDetails?.email_reminders ?? true,
//     sms_reminders: location.state?.eventDetails?.sms_reminders || false
//   });

//   // Effect to update form data when URL parameters or state change
//   useEffect(() => {
//     setFormData(prev => ({
//       ...prev,
//       start_datetime: startFromQuery,
//       end_datetime: endFromQuery
//     }));
//   }, [startFromQuery, endFromQuery]);

//   // Initialize attendees from location.state or empty
//   const initialAttendees = location.state?.attendees?.map((attendee: any) => ({
//     lead_id: attendee.lead_id || "",
//     searchTerm: attendee.name || "",
//     lead: {
//       id: attendee.lead_id,
//       full_name: attendee.name,
//       email: attendee.email,
//       company: attendee.company,
//       job_title: attendee.job_title,
//       phone: ""
//     },
//     showDropdown: false
//   })) || [{ lead_id: '', searchTerm: '', lead: null, showDropdown: true }];

//   const [attendees, setAttendees] = useState(initialAttendees);
//   const [conflicts, setConflicts] = useState([]);
//   const [showConflicts, setShowConflicts] = useState(false);

//   // Set searchTerm if lead is pre-selected
//   useEffect(() => {
//     if (formData.lead_name) {
//       setSearchTerm(formData.lead_name);
//       setShowLeadResults(false);
//     }
//   }, [formData.lead_name]);

//   // Fetch leads when component mounts
//   useEffect(() => {
//     const fetchLeads = async () => {
//       try {
//         const response = await leadApi.getLeads();
//         setLeads(response.leads);
//       } catch (error) {
//         console.error('Error fetching leads:', error);
//         toast.error('Failed to fetch leads');
//       }
//     };
//     fetchLeads();
//   }, []);

//   useEffect(() => {
//     // Filter leads based on search term
//     if (searchTerm.trim() === '') {
//       setFilteredLeads([]);
//       setShowLeadResults(false);
//       return;
//     }

//     const searchTermLower = searchTerm.toLowerCase();
//     const filtered = leads.filter(lead => {
//       return (
//         lead.full_name?.toLowerCase().includes(searchTermLower) ||
//         lead.email?.toLowerCase().includes(searchTermLower) ||
//         lead.company?.toLowerCase().includes(searchTermLower) ||
//         lead.phone?.toLowerCase().includes(searchTermLower) ||
//         lead.job_title?.toLowerCase().includes(searchTermLower) ||
//         lead.city?.toLowerCase().includes(searchTermLower) ||
//         lead.country?.toLowerCase().includes(searchTermLower)
//       );
//     });
//     setFilteredLeads(filtered);
//     setShowLeadResults(true);
//   }, [searchTerm, leads]);

//   const handleAttendeeLeadSelect = (index: number, lead: any) => {
//     setAttendees(prev => prev.map((a, i) =>
//       i === index ? { lead_id: lead.id.toString(), searchTerm: lead.full_name, lead, showDropdown: false } : a
//     ));
//   };

//   const handleAttendeeSearch = (index: number, value: string) => {
//     setAttendees(prev => prev.map((a, i) =>
//       i === index ? { ...a, searchTerm: value, showDropdown: true } : a
//     ));
//   };

//   const handleAttendeeChange = (index: number) => {
//     setAttendees(prev => prev.map((a, i) =>
//       i === index ? { ...a, showDropdown: true, searchTerm: '', lead: null, lead_id: '' } : a
//     ));
//   };

//   const addAttendee = () => {
//     setAttendees([...attendees, { lead_id: '', searchTerm: '', lead: null, showDropdown: true }]);
//   };

//   const removeAttendee = (index: number) => {
//     setAttendees(attendees.filter((_, i) => i !== index));
//   };

//   const getFilteredLeads = (searchTerm: string, selectedIds: string[]) => {
//     if (!searchTerm.trim()) return [];
//     const lower = searchTerm.toLowerCase();
//     return leads.filter(
//       l =>
//         !selectedIds.includes(l.id.toString()) &&
//         (l.full_name?.toLowerCase().includes(lower) ||
//           l.email?.toLowerCase().includes(lower) ||
//           l.company?.toLowerCase().includes(lower) ||
//           l.phone?.toLowerCase().includes(lower) ||
//           l.job_title?.toLowerCase().includes(lower))
//     );
//   };

//   const validateDateTimes = (start: string, end: string) => {
//     if (!start || !end) return true;
//     const startDate = new Date(start);
//     const endDate = new Date(end);
//     return endDate > startDate;
//   };

//   const handleDateTimeChange = (field: 'start_datetime' | 'end_datetime', value: string) => {
//     const newFormData = { ...formData, [field]: value };
    
//     // If both dates are set, validate them
//     if (newFormData.start_datetime && newFormData.end_datetime) {
//       const isValid = validateDateTimes(newFormData.start_datetime, newFormData.end_datetime);
//       if (!isValid) {
//         toast.error('End time must be after start time');
//       }
//     }
    
//     setFormData(newFormData);
//   };

//   const checkConflicts = async () => {
//     try {
//       const api = calendarApi();
//       const response = await api.checkEventConflicts(0); // 0 for new event
//       setConflicts(response.conflicts || []);
//       setShowConflicts(true);
//     } catch (error) {
//       console.error('Error checking conflicts:', error);
//       toast.error('Failed to check for conflicts');
//     }
//   };

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();

//     // Validate datetime fields
//     const startDate = new Date(formData.start_datetime);
//     const endDate = new Date(formData.end_datetime);

//     if (endDate <= startDate) {
//       toast.error('End time must be after start time');
//       return;
//     }

//     // Validate required fields
//     if (!formData.title || !formData.event_type || !formData.start_datetime || !formData.end_datetime) {
//       toast.error('Please fill in all required fields');
//       return;
//     }

//     setIsLoading(true);

//     try {
//       const api = calendarApi();
      
//       // Prepare the event data with only necessary fields
//       const eventData = {
//         // Required fields
//         title: formData.title,
//         start_datetime: formData.start_datetime,
//         end_datetime: formData.end_datetime,
//         event_type: formData.event_type,
        
//         // Optional fields - only include if they have values
//         description: formData.description || undefined,
//         timezone: formData.timezone,
//         all_day: formData.all_day,
//         priority: formData.priority || undefined,
//         location: formData.location || undefined,
//         meeting_url: formData.meeting_url || undefined,
        
//         // Lead related fields - only include if lead is selected
//         ...(formData.lead_id && {
//           lead_id: parseInt(formData.lead_id),
//           lead_name: formData.lead_name,
//           lead_email: formData.lead_email,
//           lead_phone: formData.lead_phone,
//           lead_company: formData.lead_company
//         }),
        
//         // Additional fields
//         notes: formData.notes || undefined,
//         reminder_minutes: formData.reminder_minutes,
//         email_reminders: formData.email_reminders,
//         sms_reminders: formData.sms_reminders,
        
//         // Include attendees only if there are any
//         ...(attendees.length > 0 && {
//           attendees: attendees
//             .filter(a => a.lead)
//             .map(a => ({
//               name: a.lead.full_name,
//               email: a.lead.email,
//               phone: a.lead.phone || undefined,
//               company: a.lead.company || undefined,
//               job_title: a.lead.job_title || undefined,
//               lead_id: a.lead.id ? parseInt(a.lead.id.toString()) : undefined,
//               is_organizer: false,
//               is_required: true
//             }))
//         })
//       };

//       await api.createEvent(eventData);
      
//       toast.success('Event created successfully');
//       navigate('/calendar');
//     } catch (error) {
//       console.error('Error creating event:', error);
//       toast.error('Failed to create event. Please try again.');
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="min-h-screen  p-4 lg:p-8">
//       <div className="max-w-4xl mx-auto space-y-6">
//         {/* Header */}
//         <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
//           <Link to="/calendar">
//             <Button variant="outline" size="sm" className="border-black text-black hover:bg-gray-50">
//               <ArrowLeft className="w-4 h-4 mr-2" />
//               Back to Calendar
//             </Button>
//           </Link>
//           <div className="flex-1">
//             <h1 className="text-2xl lg:text-3xl font-bold text-black flex items-center">
//               <Plus className="w-8 h-8 mr-3" />
//               Create Event
//             </h1>
//             <p className="text-gray-600 mt-1">Schedule a new event or meeting</p>
//           </div>
//         </div>

//         <form onSubmit={handleSubmit} className="space-y-6">
//           {/* Basic Event Information */}
//           <Card className="border-black ">
//             <CardHeader>
//               <CardTitle className="text-black flex items-center">
//                 <Calendar className="w-5 h-5 mr-2" />
//                 Event Details
//               </CardTitle>
//               <CardDescription>Basic information about the event</CardDescription>
//             </CardHeader>
//             <CardContent className="space-y-4">
//               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//                 <div className="md:col-span-2">
//                   <Label htmlFor="title" className="text-black">Title *</Label>
//                   <Input
//                     id="title"
//                     value={formData.title}
//                     onChange={(e) => setFormData({...formData, title: e.target.value})}
//                     placeholder="Enter event title"
//                     className="border-black focus:ring-black"
//                     required
//                   />
//                 </div>
//                 <div className="md:col-span-2">
//                   <Label htmlFor="description" className="text-black">Description</Label>
//                   <Textarea
//                     id="description"
//                     value={formData.description}
//                     onChange={(e) => setFormData({...formData, description: e.target.value})}
//                     placeholder="Enter event description"
//                     className="border-black focus:ring-black"
//                     rows={3}
//                   />
//                 </div>

//                 {/* Lead Selection */}
//                 <div className="md:col-span-2 relative">
//                   <Label className="text-black">Lead</Label>
//                   <div className="relative">
//                     <Input
//                       type="text"
//                       value={searchTerm}
//                       onChange={(e) => setSearchTerm(e.target.value)}
//                       placeholder="Search leads by name, email, company..."
//                       className="border-black focus:ring-black pr-10"
//                     />
//                     {searchTerm && (
//                       <button
//                         type="button"
//                         onClick={() => {
//                           setSearchTerm('');
//                           setFormData({
//                             ...formData,
//                             lead_id: '',
//                             lead_name: '',
//                             lead_email: '',
//                             lead_phone: '',
//                             lead_company: ''
//                           });
//                         }}
//                         className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
//                       >
//                         <X className="h-4 w-4" />
//                       </button>
//                     )}
//                   </div>
                  
//                   {showLeadResults && filteredLeads.length > 0 && (
//                     <div className="absolute z-50 mt-1 w-full  rounded-md shadow-lg border border-gray-200 max-h-60 overflow-auto">
//                       <div className="p-2">
//                         {filteredLeads.map((lead) => (
//                           <button
//                             key={lead.id}
//                             type="button"
//                             onClick={() => {
//                               setFormData({
//                                 ...formData,
//                                 lead_id: lead.id.toString(),
//                                 lead_name: lead.full_name,
//                                 lead_email: lead.email,
//                                 lead_phone: lead.phone,
//                                 lead_company: lead.company
//                               });
//                               setSearchTerm(lead.full_name);
//                               setShowLeadResults(false);
//                             }}
//                             className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors flex flex-col"
//                           >
//                             <span className="font-medium">{lead.full_name}</span>
//                             <span className="text-sm text-gray-500">
//                               {lead.company} • {lead.email}
//                             </span>
//                             <span className="text-xs text-gray-400">
//                               {[
//                                 lead.job_title,
//                                 lead.phone,
//                                 `${lead.city}${lead.country ? `, ${lead.country}` : ''}`
//                               ].filter(Boolean).join(' • ')}
//                             </span>
//                           </button>
//                         ))}
//                       </div>
//                     </div>
//                   )}
                  
//                   {showLeadResults && filteredLeads.length === 0 && searchTerm && (
//                     <div className="absolute z-50 mt-1 w-full  rounded-md shadow-lg border border-gray-200">
//                       <div className="p-4 text-center text-gray-500">
//                         No leads found matching "{searchTerm}"
//                       </div>
//                     </div>
//                   )}
                  
//                   {formData.lead_id && (
//                     <div className="mt-2 p-2 bg-gray-50 rounded-md">
//                       <div className="text-sm">
//                         <span className="font-medium">Selected Lead: </span>
//                         {formData.lead_name}
//                       </div>
//                       <div className="text-xs text-gray-500">
//                         {formData.lead_company} • {formData.lead_email} • {formData.lead_phone}
//                       </div>
//                     </div>
//                   )}
//                 </div>
//                 <div>
//                   <Label htmlFor="start_datetime" className="text-black">Start Date & Time *</Label>
//                   <Input
//                     id="start_datetime"
//                     type="datetime-local"
//                     value={formData.start_datetime}
//                     onChange={(e) => handleDateTimeChange('start_datetime', e.target.value)}
//                     className="border-black focus:ring-black"
//                     required
//                   />
//                 </div>
//                 <div>
//                   <Label htmlFor="end_datetime" className="text-black">End Date & Time *</Label>
//                   <Input
//                     id="end_datetime"
//                     type="datetime-local"
//                     value={formData.end_datetime}
//                     onChange={(e) => handleDateTimeChange('end_datetime', e.target.value)}
//                     className="border-black focus:ring-black"
//                     required
//                   />
//                 </div>
//                 <div>
//                   <Label htmlFor="event_type" className="text-black">Event Type *</Label>
//                   <Select value={formData.event_type} onValueChange={(value) => setFormData({...formData, event_type: value})}>
//                     <SelectTrigger className="border-black">
//                       <SelectValue placeholder="Select event type" />
//                     </SelectTrigger>
//                     <SelectContent>
//                       <SelectItem value="meeting">Meeting</SelectItem>
//                       <SelectItem value="call">Call</SelectItem>
//                       <SelectItem value="demo">Demo</SelectItem>
//                       <SelectItem value="follow_up">Follow-up</SelectItem>
//                       <SelectItem value="presentation">Presentation</SelectItem>
//                     </SelectContent>
//                   </Select>
//                 </div>
//                 <div>
//                   <Label htmlFor="priority" className="text-black">Priority *</Label>
//                   <Select value={formData.priority} onValueChange={(value) => setFormData({...formData, priority: value})}>
//                     <SelectTrigger className="border-black">
//                       <SelectValue placeholder="Select priority" />
//                     </SelectTrigger>
//                     <SelectContent>
//                       <SelectItem value="low">Low</SelectItem>
//                       <SelectItem value="medium">Medium</SelectItem>
//                       <SelectItem value="high">High</SelectItem>
//                       <SelectItem value="urgent">Urgent</SelectItem>
//                     </SelectContent>
//                   </Select>
//                 </div>
//                 <div>
//                   <Label htmlFor="location" className="text-black">Location</Label>
//                   <Input
//                     id="location"
//                     value={formData.location}
//                     onChange={(e) => setFormData({...formData, location: e.target.value})}
//                     placeholder="Enter location or 'Virtual'"
//                     className="border-black focus:ring-black"
//                   />
//                 </div>
//                 <div>
//                   <Label htmlFor="meeting_url" className="text-black">Meeting URL</Label>
//                   <Input
//                     id="meeting_url"
//                     type="url"
//                     value={formData.meeting_url}
//                     onChange={(e) => setFormData({...formData, meeting_url: e.target.value})}
//                     placeholder="https://..."
//                     className="border-black focus:ring-black"
//                   />
//                 </div>
//               </div>
//             </CardContent>
//           </Card>

//           {/* Attendees Section */}
//           <Card className="border-black ">
//             <CardHeader>
//               <CardTitle className="text-black flex items-center">
//                 <User className="w-5 h-5 mr-2" />
//                 Attendees
//               </CardTitle>
//               <CardDescription>Select leads as attendees for this event</CardDescription>
//             </CardHeader>
//             <CardContent className="space-y-4">
//               {attendees.map((attendee, index) => {
//                 const selectedIds = attendees.map(a => a.lead_id).filter(id => id && id !== attendee.lead_id);
//                 const filteredLeads = getFilteredLeads(attendee.searchTerm, selectedIds);
//                 return (
//                   <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-2 relative">
//                     <Label className="text-black">Attendee {index + 1}</Label>
//                     <div className="relative">
//                       <Input
//                         type="text"
//                         value={attendee.searchTerm}
//                         onChange={e => handleAttendeeSearch(index, e.target.value)}
//                         placeholder="Search leads by name, email, company..."
//                         className="border-black focus:ring-black pr-10"
//                         autoComplete="off"
//                         disabled={!attendee.showDropdown}
//                       />
//                       {attendee.showDropdown && attendee.searchTerm && filteredLeads.length > 0 && (
//                         <div className="absolute z-50 mt-1 w-full  rounded-md shadow-lg border border-gray-200 max-h-60 overflow-auto">
//                           <div className="p-2">
//                             {filteredLeads.map((lead) => (
//                               <button
//                                 key={lead.id}
//                                 type="button"
//                                 onClick={() => handleAttendeeLeadSelect(index, lead)}
//                                 className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors flex flex-col"
//                               >
//                                 <span className="font-medium">{lead.full_name}</span>
//                                 <span className="text-sm text-gray-500">
//                                   {lead.company} • {lead.email}
//                                 </span>
//                                 <span className="text-xs text-gray-400">
//                                   {[lead.job_title, lead.phone].filter(Boolean).join(' • ')}
//                                 </span>
//                               </button>
//                             ))}
//                           </div>
//                         </div>
//                       )}
//                     </div>
//                     {attendee.lead && !attendee.showDropdown && (
//                       <div className="mt-2 p-2 bg-gray-50 rounded-md flex items-center justify-between">
//                         <div>
//                           <div className="text-sm">
//                             <span className="font-medium">{attendee.lead.full_name}</span> ({attendee.lead.email})
//                           </div>
//                           <div className="text-xs text-gray-500">
//                             {attendee.lead.company} • {attendee.lead.job_title} • {attendee.lead.phone}
//                           </div>
//                         </div>
//                         <Button type="button" variant="outline" size="sm" onClick={() => handleAttendeeChange(index)} className="ml-2">Change</Button>
//                       </div>
//                     )}
//                     {attendees.length > 1 && (
//                       <Button
//                         type="button"
//                         variant="outline"
//                         size="sm"
//                         onClick={() => removeAttendee(index)}
//                         className="border-red-300 text-red-700 hover:bg-red-50 absolute top-2 right-2"
//                       >
//                         <X className="h-4 w-4" />
//                       </Button>
//                     )}
//                   </div>
//                 );
//               })}
//               <Button
//                 type="button"
//                 variant="outline"
//                 onClick={addAttendee}
//                 className="border-black text-black hover:bg-gray-50"
//               >
//                 <Plus className="w-4 h-4 mr-2" />
//                 Add Attendee
//               </Button>
//             </CardContent>
//           </Card>

//           {/* Conflict Check */}
//           {showConflicts && conflicts.length > 0 && (
//             <Card className="border-red-300 bg-red-50">
//               <CardHeader>
//                 <CardTitle className="text-red-700 flex items-center">
//                   <AlertTriangle className="w-5 h-5 mr-2" />
//                   Schedule Conflicts
//                 </CardTitle>
//                 <CardDescription className="text-red-600">
//                   The following events conflict with your selected time
//                 </CardDescription>
//               </CardHeader>
//               <CardContent>
//                 <div className="space-y-2">
//                   {conflicts.map((conflict: any) => (
//                     <div key={conflict.id} className=" border border-red-200 rounded p-3">
//                       <div className="font-medium text-red-700">{conflict.title}</div>
//                       <div className="text-sm text-red-600">
//                         {conflict.start_datetime} - {conflict.end_datetime}
//                       </div>
//                     </div>
//                   ))}
//                 </div>
//               </CardContent>
//             </Card>
//           )}

//           {/* Action Buttons */}
//           <div className="flex flex-col sm:flex-row gap-4 justify-end">
//             <Button
//               type="button"
//               variant="outline"
//               onClick={checkConflicts}
//               className="border-black text-black hover:bg-gray-50"
//               disabled={isLoading}
//             >
//               <Clock className="w-4 h-4 mr-2" />
//               Check Conflicts
//             </Button>
//             <Button
//               type="submit"
//               className="bg-black text-white hover:bg-gray-800"
//               disabled={isLoading}
//             >
//               {isLoading ? (
//                 <>
//                   <Loader2 className="w-4 h-4 mr-2 animate-spin" />
//                   Creating...
//                 </>
//               ) : (
//                 'Create Event'
//               )}
//             </Button>
//           </div>
//         </form>
//       </div>
//     </div>
//   );
// };

// export default CreateEvent;