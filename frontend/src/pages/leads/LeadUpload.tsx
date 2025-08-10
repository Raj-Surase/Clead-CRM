import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Loader2 } from "lucide-react";
import { fileApi } from "@/lib/fileApi";
import { Skeleton } from "@/components/ui/skeleton";

const LeadUpload = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [encoding, setEncoding] = useState("utf-8");
  const [delimiter, setDelimiter] = useState(",");
  const [sheetName, setSheetName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
    setSuccessMessage(null);
    try {
      await fileApi.uploadFile(selectedFile, {
        encoding,
        delimiter,
        sheet_name: sheetName || undefined,
      });
      setSuccessMessage("Upload successful. File has been processed.");
      setSelectedFile(null);
      setSheetName("");
      setEncoding("utf-8");
      setDelimiter(",");
    } catch (error: any) {
      setErrorMessage(error.message || "An error occurred while processing your file");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-8 min-h-screen space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload Lead File</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isUploading ? (
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <>
              <div>
                <Label>File</Label>
                <Input
                  type="file"
                  onChange={handleFileChange}
                  accept=".csv,.json,.xlsx,.xls"
                  className="rounded-2xl border-0 bg-muted/50"
                />
              </div>
              <div>
                <Label>File Encoding</Label>
                <select
                  value={encoding}
                  onChange={e => setEncoding(e.target.value)}
                  className="rounded-2xl border-0 bg-muted/50 w-full"
                >
                  <option value="utf-8">UTF-8</option>
                  <option value="iso-8859-1">ISO-8859-1</option>
                  <option value="windows-1252">Windows-1252</option>
                </select>
              </div>
              <div>
                <Label>CSV Delimiter</Label>
                <select
                  value={delimiter}
                  onChange={e => setDelimiter(e.target.value)}
                  className="rounded-2xl border-0 bg-muted/50 w-full"
                >
                  <option value=",">Comma (,)</option>
                  <option value=";">Semicolon (;)</option>
                  <option value="|">Pipe (|)</option>
                  <option value="\t">Tab</option>
                </select>
              </div>
              <div>
                <Label>Excel Sheet Name (Optional)</Label>
                <Input
                  value={sheetName}
                  onChange={e => setSheetName(e.target.value)}
                  placeholder="For Excel files, specify sheet name"
                  className="rounded-2xl border-0 bg-muted/50"
                />
              </div>
              {errorMessage && (
                <div className="p-2 rounded-2xl bg-destructive/10 text-destructive text-sm">{errorMessage}</div>
              )}
              {successMessage && (
                <div className="p-2 rounded-2xl bg-green-100 text-green-700 text-sm">{successMessage}</div>
              )}
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="w-full"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload File
                  </>
                )}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LeadUpload;