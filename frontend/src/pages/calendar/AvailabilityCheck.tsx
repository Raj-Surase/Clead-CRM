// import { useState } from "react";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
// import { Badge } from "@/components/ui/badge";
// import { Clock, ArrowLeft, Calendar, Search, Plus, Loader2 } from "lucide-react";
// import { Link } from "react-router-dom";
// import { calendarApi } from "@/lib/calendarApi";
// import { toast } from "sonner";

// interface TimeSlot {
//   start_datetime: string;
//   end_datetime: string;
//   is_available: boolean;
//   conflicting_event_id: number | null;
//   conflicting_event_title: string | null;
// }

// interface SlotsByDay {
//   [key: string]: TimeSlot[];
// }

// interface AvailabilityResponse {
//   start_date: string;
//   end_date: string;
//   timezone: string;
//   slots_by_day: SlotsByDay;
//   total_slots: number;
//   available_count: number;
//   busy_count: number;
// }

// const AvailabilityCheck = () => {
//   const [formData, setFormData] = useState({
//     start_date: "",
//     end_date: "",
//     duration_minutes: 0,
//     timezone: "",
//     buffer_minutes: 0
//   });
  

//   const [isLoading, setIsLoading] = useState(false);
//   const [availabilityData, setAvailabilityData] = useState<AvailabilityResponse | null>(null);
//   const [showResults, setShowResults] = useState(false);

//   const checkAvailability = async () => {
//     if (!formData.start_date || !formData.end_date) {
//       toast.error('Please select both start and end dates');
//       return;
//     }

//     setIsLoading(true);
//     try {
//       const api = calendarApi();
//       const endDate = new Date(formData.end_date);
//       endDate.setDate(endDate.getDate() + 1);

//       const response = await api.checkAvailability({
//         start_date: `${formData.start_date}T00:00:00Z`,
//         end_date: `${endDate.toISOString().split('T')[0]}T00:00:00Z`,
//         duration_minutes: formData.duration_minutes,
//         timezone: formData.timezone,
//         buffer_minutes: formData.buffer_minutes
//       });
//       setAvailabilityData(response as unknown as AvailabilityResponse);
//       setShowResults(true);
//     } catch (error) {
//       console.error('Error checking availability:', error);
//       toast.error('Failed to check availability');
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const formatTime = (dateTimeString: string) => {
//     return new Date(dateTimeString).toLocaleTimeString('en-US', {
//       hour: '2-digit',
//       minute: '2-digit',
//       hour12: true
//     });
//   };

//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleDateString('en-US', {
//       weekday: 'long',
//       year: 'numeric',
//       month: 'long',
//       day: 'numeric'
//     });
//   };

//   return (
//     <div className="min-h-screen  p-4 lg:p-8">
//       <div className="max-w-6xl mx-auto space-y-6">
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
//               <Clock className="w-8 h-8 mr-3" />
//               Availability Check
//             </h1>
//             <p className="text-gray-600 mt-1">Find available time slots for scheduling</p>
//           </div>
//         </div>

//         {/* Search Form */}
//         <Card className="border-black ">
//           <CardHeader>
//             <CardTitle className="text-black flex items-center">
//               <Search className="w-5 h-5 mr-2" />
//               Search Availability
//             </CardTitle>
//             <CardDescription>Set your preferences to find available time slots</CardDescription>
//           </CardHeader>
//           <CardContent className="space-y-4">
//             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//               <div>
//                 <Label htmlFor="start_date" className="text-black">Start Date *</Label>
//                 <Input
//                   id="start_date"
//                   type="date"
//                   value={formData.start_date}
//                   onChange={(e) => setFormData({...formData, start_date: e.target.value})}
//                   className="border-black focus:ring-black"
//                   required
//                 />
//               </div>
//               <div>
//                 <Label htmlFor="end_date" className="text-black">End Date *</Label>
//                 <Input
//                   id="end_date"
//                   type="date"
//                   value={formData.end_date}
//                   onChange={(e) => setFormData({...formData, end_date: e.target.value})}
//                   className="border-black focus:ring-black"
//                   required
//                 />
//               </div>
//               <div>
//                 <Label htmlFor="duration_minutes" className="text-black">Duration (minutes) *</Label>
//                 <Select value={formData.duration_minutes.toString()} onValueChange={(value) => setFormData({...formData, duration_minutes: parseInt(value)})}>
//                   <SelectTrigger className="border-black">
//                     <SelectValue />
//                   </SelectTrigger>
//                   <SelectContent>
//                     <SelectItem value="15">15 minutes</SelectItem>
//                     <SelectItem value="30">30 minutes</SelectItem>
//                     <SelectItem value="45">45 minutes</SelectItem>
//                     <SelectItem value="60">1 hour</SelectItem>
//                   </SelectContent>
//                 </Select>
//               </div>
//               <div>
//                 <Label htmlFor="buffer_minutes" className="text-black">Buffer Minutes</Label>
//                 <Input
//                   id="buffer_minutes"
//                   type="number"
//                   value={formData.buffer_minutes}
//                   onChange={(e) => setFormData({...formData, buffer_minutes: parseInt(e.target.value) || 0})}
//                   placeholder="15"
//                   className="border-black focus:ring-black"
//                 />
//               </div>
//             </div>
            
//             <Button
//               onClick={checkAvailability}
//               className="bg-black text-white hover:bg-gray-800 w-full"
//               disabled={isLoading}
//             >
//               {isLoading ? (
//                 <>
//                   <Loader2 className="w-4 h-4 mr-2 animate-spin" />
//                   Checking Availability...
//                 </>
//               ) : (
//                 <>
//                   <Search className="w-4 h-4 mr-2" />
//                   Check Availability
//                 </>
//               )}
//             </Button>
//           </CardContent>
//         </Card>

//         {/* Results */}
//         {showResults && availabilityData && (
//           <>
//             {/* Summary Stats */}
//             <Card className="border-black ">
//               <CardHeader>
//                 <CardTitle className="text-black">Availability Summary</CardTitle>
//               </CardHeader>
//               <CardContent>
//                 <div className="grid grid-cols-3 gap-4">
//                   <div className="text-center">
//                     <div className="text-2xl font-bold text-green-600">{availabilityData.available_count}</div>
//                     <div className="text-sm text-gray-600">Available Slots</div>
//                   </div>
//                   <div className="text-center">
//                     <div className="text-2xl font-bold text-red-600">{availabilityData.busy_count}</div>
//                     <div className="text-sm text-gray-600">Busy Slots</div>
//                   </div>
//                   <div className="text-center">
//                     <div className="text-2xl font-bold text-blue-600">{availabilityData.total_slots}</div>
//                     <div className="text-sm text-gray-600">Total Slots</div>
//                   </div>
//                 </div>
//               </CardContent>
//             </Card>

//             {/* Slots by Day */}
//             {Object.entries(availabilityData.slots_by_day).map(([date, slots]) => (
//               <Card key={date} className="border-black ">
//                 <CardHeader>
//                   <CardTitle className="text-black flex items-center">
//                     <Calendar className="w-5 h-5 mr-2" />
//                     {formatDate(date)}
//                   </CardTitle>
//                   <CardDescription>
//                     {slots.filter(slot => slot.is_available).length} available slots
//                   </CardDescription>
//                 </CardHeader>
//                 <CardContent>
//                   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
//                     {slots.map((slot, index) => (
//                       <div
//                         key={index}
//                         className={`border rounded-lg p-3 ${
//                           slot.is_available 
//                             ? 'border-green-200 bg-green-50' 
//                             : 'border-red-200 bg-red-50'
//                         }`}
//                       >
//                         <div className="flex items-center justify-between mb-2">
//                           <div className="font-medium text-black">
//                             {formatTime(slot.start_datetime)} - {formatTime(slot.end_datetime)}
//                           </div>
//                           <Badge className={
//                             slot.is_available 
//                               ? 'bg-green-100 text-green-700 border-green-200' 
//                               : 'bg-red-100 text-red-700 border-red-200'
//                           }>
//                             {slot.is_available ? 'Available' : 'Busy'}
//                           </Badge>
//                         </div>
//                         {slot.conflicting_event_title && (
//                           <div className="text-sm text-red-600 mt-1">
//                             {slot.conflicting_event_title}
//                           </div>
//                         )}
//                         {slot.is_available && (
//                           <Link 
//                             to={{
//                               pathname: "/calendar/events/create",
//                               search: `?start=${encodeURIComponent(slot.start_datetime)}&end=${encodeURIComponent(slot.end_datetime)}`
//                             }}
//                             state={{ 
//                               eventDetails: {
//                                 start_datetime: slot.start_datetime,
//                                 end_datetime: slot.end_datetime
//                               }
//                             }}
//                           >
//                             <Button size="sm" className="w-full mt-2 bg-green-600 text-white hover:bg-green-700">
//                               <Plus className="w-3 h-3 mr-1" />
//                               Schedule
//                             </Button>
//                           </Link>
//                         )}
//                       </div>
//                     ))}
//                   </div>
//                 </CardContent>
//               </Card>
//             ))}
//           </>
//         )}
//       </div>
//     </div>
//   );
// };

// export default AvailabilityCheck;