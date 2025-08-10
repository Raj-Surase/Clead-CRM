import { useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import LeadParser from "./LeadParser";
import LeadHistory from "./LeadHistory";
import { Button } from "@/components/ui/button";
import { Plus, Upload } from "lucide-react";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useForm } from "react-hook-form";
import { fileApi, leadApi, authApi } from "@/lib/api";
import { FileText } from "lucide-react";

const LeadsModule = () => {
  const [activeTab, setActiveTab] = useState("leads");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [encoding, setEncoding] = useState("utf-8");
  const [delimiter, setDelimiter] = useState(",");
  const [sheetName, setSheetName] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const { toast } = useToast();
  const leadParserRef = useRef<{ refresh: () => void }>(null);

  const form = useForm({
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      mobile: "",
      company: "",
      job_title: "",
      industry: "",
      city: "",
      country: "",
      linkedin_url: "",
      facebook_url: "",
      instagram_url: "",
      twitter_url: "",
      youtube_url: "",
      tiktok_url: "",
      website: "",
      tags: "",
    },
  });

  const openCreateDialog = () => {
    setEditMode(false);
    setSelectedLead(null);
    form.reset({
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      mobile: "",
      company: "",
      job_title: "",
      industry: "",
      city: "",
      country: "",
      linkedin_url: "",
      facebook_url: "",
      instagram_url: "",
      twitter_url: "",
      youtube_url: "",
      tiktok_url: "",
      website: "",
      tags: "",
    });
    setCreateDialogOpen(true);
  };

  const openEditDialog = (lead: any) => {
    setEditMode(true);
    setSelectedLead(lead);
    form.reset({
      first_name: lead.first_name || "",
      last_name: lead.last_name || "",
      email: lead.email || "",
      phone: lead.phone || "",
      mobile: lead.mobile || "",
      company: lead.company || "",
      job_title: lead.job_title || "",
      industry: lead.industry || "",
      city: lead.city || "",
      country: lead.country || "",
      linkedin_url: lead.linkedin_url || "",
      facebook_url: lead.facebook_url || "",
      instagram_url: lead.instagram_url || "",
      twitter_url: lead.twitter_url || "",
      youtube_url: lead.youtube_url || "",
      tiktok_url: lead.tiktok_url || "",
      website: lead.website || "",
      tags: lead.tags || "",
    });
    setCreateDialogOpen(true);
  };

  const onSubmit = async (values: any) => {
    try {
      const userId = await authApi.getUserId();
      if (editMode && selectedLead) {
        await leadApi.updateLead(selectedLead.id, { ...values, user_id: userId });
        toast({ title: "Lead updated", description: `${values.first_name} ${values.last_name}` });
      } else {
        await leadApi.createLead({ ...values, user_id: userId });
        toast({ title: "Lead created", description: `${values.first_name} ${values.last_name}` });
      }
      setCreateDialogOpen(false);
      setSelectedLead(null);
      setEditMode(false);
      // Trigger refresh in LeadParser component
      if (leadParserRef.current) {
        leadParserRef.current.refresh();
      }
    } catch (e: any) {
      toast({ title: "Save failed", description: e.message, variant: "destructive" });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedTypes = ['.csv', '.json', '.xlsx', '.xls'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (allowedTypes.includes(fileExtension)) {
        setSelectedFile(file);
        setErrorMessage(null);
      } else {
        alert('Please select a valid file type (CSV, JSON, XLSX, XLS)');
        e.target.value = '';
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMessage(null);
    try {
      await fileApi.uploadFile(selectedFile, {
        encoding,
        delimiter,
        sheet_name: sheetName || undefined,
      });
      toast({ title: "Upload successful", description: "File has been processed." });
      setUploadDialogOpen(false);
      clearUploadForm();
      // Trigger refresh in LeadParser component
      if (leadParserRef.current) {
        leadParserRef.current.refresh();
      }
    } catch (error: any) {
      setErrorMessage(error.message || "An error occurred while processing your file");
      toast({ title: "Upload failed", description: error.message, variant: "destructive" });
    } finally {
      setIsUploading(false);
    }
  };

  const clearUploadForm = () => {
    setSelectedFile(null);
    setSheetName("");
    setEncoding("utf-8");
    setDelimiter(",");
    setErrorMessage(null);
  };

  return (
    <div className="p-8 min-h-screen space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Lead Management</h1>
          <p className="text-muted-foreground">Manage and analyze your leads efficiently</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <Button onClick={openCreateDialog}>
              <Plus className="w-4 h-4 mr-2" /> Create Lead
            </Button>
            <Button onClick={() => setUploadDialogOpen(true)}>
              <Upload className="w-4 h-4 mr-2" />
              Upload File
            </Button>
          </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-muted/50 p-1">
          <TabsTrigger value="leads" className="flex-1">Leads</TabsTrigger>
          <TabsTrigger value="history" className="flex-1">File History</TabsTrigger>
        </TabsList>
        
        <TabsContent value="leads" className="space-y-6">
          <LeadParser ref={leadParserRef} onEditLead={openEditDialog} />
        </TabsContent>
        
        <TabsContent value="history" className="space-y-6">
          <LeadHistory />
        </TabsContent>
      </Tabs>

      {/* Create/Edit Lead Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="rounded-3xl max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editMode ? "Edit Lead" : "Create Lead"}</DialogTitle>
            <DialogDescription>
              {editMode ? "Update the lead information." : "Enter details to create a new lead."}
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField name="first_name" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>First Name</FormLabel>
                    <FormControl>
                      <Input {...field} className="rounded-2xl border-0 bg-muted/50" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="last_name" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last Name</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="email" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl><Input type="email" {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="phone" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="mobile" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mobile</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="company" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Company</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="job_title" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Job Title</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="industry" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Industry</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="city" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>City</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="country" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Country</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="linkedin_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>LinkedIn URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="facebook_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Facebook URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="instagram_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Instagram URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="twitter_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Twitter URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="youtube_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>YouTube URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="tiktok_url" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>TikTok URL</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField name="website" control={form.control} render={({ field }) => (
                  <FormItem>
                    <FormLabel>Website</FormLabel>
                    <FormControl><Input {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
              <FormField name="tags" control={form.control} render={({ field }) => (
                <FormItem>
                  <FormLabel>Tags</FormLabel>
                  <FormControl><Input {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <DialogFooter className="gap-2">
                <Button 
                  variant="outline"
                  onClick={() => setCreateDialogOpen(false)}
                  className="rounded-2xl border-0 bg-muted/50"
                  type="button"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="rounded-2xl"
                >
                  {editMode ? "Update Lead" : "Create Lead"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Upload File Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={open => { setUploadDialogOpen(open); if (!open) clearUploadForm(); }}>
        <DialogContent className="rounded-3xl max-w-2xl">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
            <DialogDescription>
              Upload a file to parse leads.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="file">Select File</Label>
              <Input
                id="file"
                type="file"
                accept=".csv,.json,.xlsx,.xls"
                onChange={handleFileChange}
                className="mt-1 rounded-2xl border-0 bg-muted/50"
              />
              <p className="text-sm text-muted-foreground mt-1">
                Supported formats: CSV, JSON, XLSX, XLS (Max 10MB)
              </p>
            </div>
            {selectedFile && (
              <div className="p-4 rounded-2xl bg-muted/50">
                <div className="flex items-center">
                  <FileText className="w-5 h-5 text-black mr-2" />
                  <div className="flex-1">
                    <p className="font-medium text-black">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="encoding">Encoding</Label>
                <select
                  id="encoding"
                  value={encoding}
                  onChange={(e) => setEncoding(e.target.value)}
                  className="mt-1 block w-full rounded-2xl border-0 bg-muted/50"
                >
                  <option value="utf-8">UTF-8</option>
                  <option value="iso-8859-1">ISO-8859-1</option>
                  <option value="windows-1252">Windows-1252</option>
                </select>
              </div>
              <div>
                <Label htmlFor="delimiter">Delimiter</Label>
                <select
                  id="delimiter"
                  value={delimiter}
                  onChange={(e) => setDelimiter(e.target.value)}
                  className="mt-1 block w-full rounded-2xl border-0 bg-muted/50"
                >
                  <option value=",">Comma (,)</option>
                  <option value=";">Semicolon (;)</option>
                  <option value="|">Pipe (|)</option>
                  <option value="\t">Tab</option>
                </select>
              </div>
            </div>
            <div>
              <Label htmlFor="sheetName">Sheet Name (Optional)</Label>
              <Input
                id="sheetName"
                value={sheetName}
                onChange={(e) => setSheetName(e.target.value)}
                placeholder="For Excel files, specify sheet name"
                className="rounded-2xl border-0 bg-muted/50"
              />
            </div>
            {errorMessage && (
              <div className="p-2 rounded-2xl bg-destructive/10 text-destructive text-sm">{errorMessage}</div>
            )}
            <DialogFooter className="gap-2">
              <Button
                onClick={clearUploadForm}
                variant="outline"
                className="rounded-2xl border-0 bg-muted/50"
                disabled={isUploading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="rounded-2xl"
              >
                <Upload className="w-4 h-4 mr-2" />
                {isUploading ? "Processing..." : "Upload & Process"}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LeadsModule; 