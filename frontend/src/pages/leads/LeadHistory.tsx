import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { History, Search, Download, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { fileApi } from "@/lib/fileApi";
import { toast, Toaster } from "sonner";
import { FileHistoryEntry, FileDeleteResponse } from "@/lib/api";

const LeadHistory = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [uploadHistory, setUploadHistory] = useState<FileHistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await fileApi.getFileHistory(50, 0); // Get last 50 entries
        setUploadHistory(history);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching history:', error);
        setIsLoading(false);
        toast.error("Failed to fetch upload history");
      }
    };

    fetchHistory();
  }, []);

  const handleDelete = async (fileId: number) => {
    setFileToDelete(fileId);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!fileToDelete) return;

    setIsDeleting(true);
    try {
      const response: FileDeleteResponse = await fileApi.deleteFile(fileToDelete);
      setUploadHistory(prev => prev.filter(item => item.id !== fileToDelete));
      toast.success(`File deleted successfully. ${response.deleted_leads_count} leads removed.`);
      setIsDeleteDialogOpen(false);
      setFileToDelete(null);
    } catch (error) {
      console.error('Error deleting file:', error);
      toast.error("Failed to delete file");
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-50 text-green-700 border-green-200";
      case "processing": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "failed": return "bg-red-50 text-red-700 border-red-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const totalPages = Math.ceil(uploadHistory.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedHistory = uploadHistory.slice(startIndex, startIndex + itemsPerPage);

  // if (isLoading) {
  //   return <div className="text-center">Loading...</div>;
  // }

  return (
    <div className="space-y-6">
      {/* <Toaster position="top-right" />
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-1">
          <p className="text-muted-foreground">View and manage your file upload history</p>
        </div>
      </div> */}

      {/* History Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg md:text-xl">File Upload History</CardTitle>
          <CardDescription className="text-sm">
            Showing {startIndex + 1}-{Math.min(startIndex + itemsPerPage, uploadHistory.length)} of {uploadHistory.length} uploads
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 font-medium min-w-32">Filename</th>
                  <th className="text-left p-3 font-medium hidden sm:table-cell min-w-20">Type</th>
                  <th className="text-left p-3 font-medium hidden md:table-cell min-w-20">Size</th>
                  {/* <th className="text-left p-3 font-medium min-w-20">Status</th>
                  <th className="text-left p-3 font-medium hidden lg:table-cell min-w-20">Rows</th>
                  <th className="text-left p-3 font-medium hidden lg:table-cell min-w-20">Leads</th> */}
                  <th className="text-left p-3 font-medium hidden xl:table-cell min-w-32">Uploaded</th>
                  <th className="text-left p-3 font-medium min-w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="text-center p-6">
                      Loading...
                    </td>
                  </tr>
                ) : (
                  paginatedHistory.map((item) => (
                    <tr key={item.id} className="border-b border-border hover:bg-accent/50">
                      <td className="p-3">
                        <div className="font-medium">{item.filename}</div>
                        <div className="text-sm text-muted-foreground sm:hidden">
                          {item.file_type} • {(item.file_size / 1024 / 1024).toFixed(2)} MB
                        </div>
                      </td>
                      <td className="p-3 text-muted-foreground hidden sm:table-cell">{item.file_type}</td>
                      <td className="p-3 text-muted-foreground hidden md:table-cell">
                        {(item.file_size / 1024 / 1024).toFixed(2)} MB
                      </td>
                      <td className="p-3 text-muted-foreground hidden xl:table-cell">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="p-3">
                        <div className="flex flex-col sm:flex-row gap-1">
                          <Button 
                            size="sm" 
                            variant="destructive" 
                            onClick={() => handleDelete(item.id)}
                            disabled={isDeleting && fileToDelete === item.id}
                            className="text-xs px-2"
                          >
                            <Trash2 className="w-3 h-3 sm:mr-1" />
                            <span className="hidden sm:inline">Delete</span>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>

            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between mt-6 gap-4">
              <div className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="rounded-2xl border-0 bg-muted/50"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span className="hidden sm:inline ml-1">Previous</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="rounded-2xl border-0 bg-muted/50"
                >
                  <span className="hidden sm:inline mr-1">Next</span>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

          {/* Delete Confirmation Dialog */}
          <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
            <DialogContent className="rounded-3xl">
              <DialogHeader>
                <DialogTitle>Confirm Deletion</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete this file and all associated leads? This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsDeleteDialogOpen(false)}
                  className="rounded-2xl border-0 bg-muted/50"
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={confirmDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
    </div>
  );
};

export default LeadHistory;