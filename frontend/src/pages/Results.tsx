import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import {
  Database,
  LogOut,
  ArrowLeft,
  FileText,
  Code2,
  BarChart3,
  Table,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  ChevronRight,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  Send,
  User,
  Bot,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useText2SQL } from "@/hooks/useText2SQL";
import { toast } from "sonner";
import { Text2SQLResponse } from "@/services/api";

/**
 * Transforms API data array into chart format
 */
function transformDataForChart(data: Array<Record<string, any>>): Array<{ name: string; value: number }> {
  if (!data || data.length === 0) return [];

  const firstRow = data[0];
  const keys = Object.keys(firstRow);

  const labelKey = keys.find(key => typeof firstRow[key] === 'string' || firstRow[key] === null);
  const valueKey = keys.find(key => typeof firstRow[key] === 'number');

  if (!valueKey) {
    return [];
  }

  return data.slice(0, 20).map((row, index) => ({
    name: labelKey ? String(row[labelKey] || `Item ${index + 1}`) : `Item ${index + 1}`,
    value: Number(row[valueKey]) || 0,
  }));
}

/**
 * Extracts table headers and data from API response
 */
function transformDataForTable(data: Array<Record<string, any>>): {
  headers: string[];
  rows: Array<Record<string, any>>;
} {
  if (!data || data.length === 0) {
    return { headers: [], rows: [] };
  }

  const headers = Object.keys(data[0]);
  return {
    headers,
    rows: data,
  };
}

interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  content: string;
  response?: Text2SQLResponse;
  timestamp: Date;
}

const Results = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const navigate = useNavigate();
  const [username, setUsername] = useState("User");
  const [activeTab, setActiveTab] = useState<"summary" | "sql" | "chart" | "table">("summary");
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [copied, setCopied] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [followUpInput, setFollowUpInput] = useState("");
  const [tablePage, setTablePage] = useState(0);
  const tableRowsPerPage = 50;
  const chatEndRef = useRef<HTMLDivElement>(null);
  const followUpMutation = useText2SQL();

  const text2sqlMutation = useText2SQL();

  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (!isLoggedIn) {
      navigate("/");
      return;
    }

    if (query.trim() && !hasInitialized) {
      setConversationHistory([{
        id: Date.now().toString(),
        type: "user",
        content: query.trim(),
        timestamp: new Date(),
      }]);

      text2sqlMutation.mutate(
        { input_text: query.trim() },
        {
          onSuccess: (data) => {
            setConversationHistory(prev => [...prev, {
              id: (Date.now() + 1).toString(),
              type: "assistant",
              content: data.summary || "Response received",
              response: data,
              timestamp: new Date(),
            }]);
          },
          onError: (error) => {
            toast.error("Failed to process query", {
              description: error.message || "An error occurred while processing your query.",
            });
          },
        }
      );
      setHasInitialized(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, navigate, hasInitialized]);

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (!isLoggedIn) {
      navigate("/");
      return;
    }
    const storedUsername = localStorage.getItem("username");
    if (storedUsername) {
      setUsername(storedUsername);
    }
  }, [navigate]);

  const latestResponse = followUpMutation.data || text2sqlMutation.data;

  const chartData = useMemo(() => {
    if (!latestResponse?.data) return [];
    return transformDataForChart(latestResponse.data);
  }, [latestResponse?.data]);

  const tableData = useMemo(() => {
    if (!latestResponse?.data) return { headers: [], rows: [] };
    return transformDataForTable(latestResponse.data);
  }, [latestResponse?.data]);

  useEffect(() => {
    setTablePage(0);
  }, [latestResponse?.data]);

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("username");
    navigate("/");
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationHistory, followUpMutation.isPending]);

  const handleFollowUp = (question: string) => {
    setConversationHistory(prev => [...prev, {
      id: Date.now().toString(),
      type: "user",
      content: question,
      timestamp: new Date(),
    }]);

    followUpMutation.mutate(
      { input_text: question },
      {
        onSuccess: (data) => {
          setConversationHistory(prev => [...prev, {
            id: (Date.now() + 1).toString(),
            type: "assistant",
            content: data.summary || "Response received",
            response: data,
            timestamp: new Date(),
          }]);

          setActiveTab("summary");
          setFeedback(null);
          setShowFeedbackForm(false);
        },
        onError: (error) => {
          toast.error("Failed to process follow-up", {
            description: error.message || "An error occurred while processing your question.",
          });
        },
      }
    );
  };

  const handleFollowUpSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (followUpInput.trim()) {
      handleFollowUp(followUpInput.trim());
      setFollowUpInput("");
    }
  };

  const copySQL = () => {
    const sqlQuery = latestResponse?.sql_query;
    if (sqlQuery) {
      navigator.clipboard.writeText(sqlQuery);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("SQL query copied to clipboard");
    }
  };

  const handleRetry = () => {
    if (query.trim()) {
      text2sqlMutation.mutate(
        { input_text: query.trim() },
        {
          onError: (error) => {
            toast.error("Failed to process query", {
              description: error.message || "An error occurred while processing your query.",
            });
          },
        }
      );
    }
  };

  const tabs = [
    { id: "summary", label: "Summary", icon: FileText },
    { id: "sql", label: "SQL Query", icon: Code2 },
    { id: "chart", label: "Visualization", icon: BarChart3 },
    { id: "table", label: "Data Table", icon: Table },
  ] as const;

  const isLoading = text2sqlMutation.isPending || followUpMutation.isPending;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button onClick={() => navigate("/home")} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <Database className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-foreground text-lg">Text2SQL</span>
          </button>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-sm font-medium text-primary-foreground">
                {username.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm text-foreground hidden sm:block">{username}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Back Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/home")}
          className="mb-6 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Search
        </Button>

        {/* Question Card */}
        <div className="bg-card border rounded-xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <MessageSquare className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Your Question</p>
              <h1 className="text-xl md:text-2xl font-semibold text-foreground">{query || "No query provided"}</h1>
            </div>
          </div>
        </div>

        {/* Empty State */}
        {!query.trim() && !text2sqlMutation.isPending && !text2sqlMutation.isError && !text2sqlMutation.isSuccess && (
          <div className="bg-card border rounded-xl p-6 mb-6">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>No query provided</AlertTitle>
              <AlertDescription className="mt-2 text-muted-foreground">
                Please go back and enter a question to get results.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-card border rounded-xl p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <RefreshCw className="w-5 h-5 text-primary animate-spin" />
              <span className="text-sm text-muted-foreground">AI is analyzing your query...</span>
            </div>
            <div className="space-y-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          </div>
        )}

        {/* Error State */}
        {(text2sqlMutation.isError || followUpMutation.isError) && !isLoading && (
          <div className="bg-card border rounded-xl p-6 mb-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error processing query</AlertTitle>
              <AlertDescription className="mt-2">
                {(followUpMutation.error || text2sqlMutation.error)?.message || "An unexpected error occurred. Please try again."}
              </AlertDescription>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                className="mt-4"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Retry
              </Button>
            </Alert>
          </div>
        )}

        {/* Results */}
        {latestResponse && !isLoading && (
          <>
            {/* Tabs */}
            <div className="flex flex-wrap gap-2 mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="bg-card border rounded-xl p-6 mb-6">
              {activeTab === "summary" && (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-muted-foreground">AI-Generated Summary</h3>
                  <p className="text-foreground leading-relaxed">
                    {latestResponse?.summary || "No summary available."}
                  </p>
                  {latestResponse?.data && (
                    <div className="flex items-center gap-4 pt-4 border-t text-sm text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <Table className="w-4 h-4" />
                        {latestResponse.data.length} rows returned
                      </span>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "sql" && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Generated SQL</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copySQL}
                      disabled={!latestResponse?.sql_query}
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                      <span className="ml-2">{copied ? "Copied!" : "Copy"}</span>
                    </Button>
                  </div>
                  <pre className="bg-muted rounded-lg p-4 overflow-x-auto">
                    <code className="text-sm text-foreground">
                      {latestResponse?.sql_query || "No SQL query available."}
                    </code>
                  </pre>
                </div>
              )}

              {activeTab === "chart" && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Data Visualization</h3>
                  <div className="h-80">
                    {chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                          <XAxis
                            dataKey="name"
                            stroke="hsl(var(--muted-foreground))"
                            fontSize={11}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                          />
                          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "hsl(var(--card))",
                              border: "1px solid hsl(var(--border))",
                              borderRadius: "8px",
                            }}
                            formatter={(value: number) => [value.toLocaleString(), "Value"]}
                          />
                          <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <div className="text-center">
                          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                          <p className="font-medium">No chart data available</p>
                          <p className="text-sm mt-1">The query results don't contain suitable data for visualization.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "table" && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Query Results</h3>
                  <div className="overflow-x-auto">
                    {tableData.rows.length > 0 ? (
                      <>
                        <table className="w-full">
                          <thead>
                            <tr className="border-b">
                              {tableData.headers.map((header, index) => (
                                <th key={index} className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {tableData.rows
                              .slice(tablePage * tableRowsPerPage, (tablePage + 1) * tableRowsPerPage)
                              .map((row, rowIndex) => (
                                <tr key={rowIndex} className="border-b hover:bg-muted/50 transition-colors">
                                  {tableData.headers.map((header, cellIndex) => {
                                    const cellValue = row[header];
                                    return (
                                      <td key={cellIndex} className="py-3 px-4 text-sm text-foreground">
                                        {cellValue === null || cellValue === undefined
                                          ? <span className="text-muted-foreground">-</span>
                                          : typeof cellValue === 'object'
                                          ? JSON.stringify(cellValue)
                                          : String(cellValue)}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                          </tbody>
                        </table>
                        {tableData.rows.length > tableRowsPerPage && (
                          <div className="flex items-center justify-between mt-4 pt-4 border-t">
                            <p className="text-sm text-muted-foreground">
                              Showing {tablePage * tableRowsPerPage + 1} - {Math.min((tablePage + 1) * tableRowsPerPage, tableData.rows.length)} of {tableData.rows.length} rows
                            </p>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setTablePage(p => Math.max(0, p - 1))}
                                disabled={tablePage === 0}
                              >
                                Previous
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setTablePage(p => p + 1)}
                                disabled={(tablePage + 1) * tableRowsPerPage >= tableData.rows.length}
                              >
                                Next
                              </Button>
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="flex items-center justify-center h-40 text-muted-foreground">
                        <div className="text-center">
                          <Table className="w-12 h-12 mx-auto mb-3 opacity-30" />
                          <p className="font-medium">No data available</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Feedback Section */}
        <div className="bg-card border rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <p className="text-sm text-muted-foreground">Was this response helpful?</p>
            <div className="flex items-center gap-2">
              <Button
                variant={feedback === "up" ? "default" : "outline"}
                size="sm"
                onClick={() => setFeedback("up")}
              >
                <ThumbsUp className="w-4 h-4 mr-2" />
                Helpful
              </Button>
              <Button
                variant={feedback === "down" ? "default" : "outline"}
                size="sm"
                onClick={() => setFeedback("down")}
              >
                <ThumbsDown className="w-4 h-4 mr-2" />
                Not Helpful
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFeedbackForm(!showFeedbackForm)}
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Feedback
              </Button>
            </div>
          </div>

          {showFeedbackForm && (
            <div className="mt-4 pt-4 border-t">
              <Textarea
                placeholder="Share your feedback or suggestions..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                className="mb-3"
                rows={3}
              />
              <Button
                size="sm"
                onClick={() => {
                  if (feedbackText.trim()) {
                    console.log("Feedback submitted:", {
                      feedback: feedback,
                      text: feedbackText,
                      query: query,
                      timestamp: new Date().toISOString(),
                    });
                    toast.success("Thank you for your feedback!");
                    setFeedbackText("");
                  }
                  setShowFeedbackForm(false);
                }}
              >
                Submit Feedback
              </Button>
            </div>
          )}
        </div>

        {/* Follow-up Questions */}
        {latestResponse && latestResponse?.followup_questions && latestResponse.followup_questions.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
              Related Questions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {latestResponse.followup_questions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleFollowUp(question)}
                  className="bg-card border rounded-xl p-4 text-left flex items-center justify-between group hover:bg-accent transition-colors"
                  disabled={isLoading}
                >
                  <span className="text-foreground group-hover:text-primary transition-colors">{question}</span>
                  <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Interface */}
        {conversationHistory.length > 0 && (
          <div className="bg-card border rounded-xl p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              Conversation
            </h2>

            {/* Chat Messages */}
            <div className="max-h-96 overflow-y-auto mb-4 space-y-4 pr-2">
              {conversationHistory.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.type === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.type === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary-foreground" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] p-4 rounded-xl ${
                      message.type === "user"
                        ? "bg-primary text-primary-foreground rounded-br-sm"
                        : "bg-muted rounded-bl-sm"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.type === "assistant" && message.response && (
                      <div className="mt-2 pt-2 border-t border-border/30">
                        <p className="text-xs text-muted-foreground">
                          {message.response.data?.length || 0} rows • Click tabs above to view details
                        </p>
                      </div>
                    )}
                  </div>
                  {message.type === "user" && (
                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-foreground" />
                    </div>
                  )}
                </div>
              ))}

              {followUpMutation.isPending && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary-foreground" />
                  </div>
                  <div className="bg-muted p-4 rounded-xl rounded-bl-sm">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-primary" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <form onSubmit={handleFollowUpSubmit} className="flex gap-2">
              <Input
                type="text"
                placeholder="Ask a follow-up question..."
                value={followUpInput}
                onChange={(e) => setFollowUpInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleFollowUpSubmit();
                  }
                }}
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                type="submit"
                disabled={!followUpInput.trim() || isLoading}
                className="shrink-0"
              >
                {followUpMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
};

export default Results;
