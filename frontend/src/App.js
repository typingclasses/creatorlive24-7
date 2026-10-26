import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Show, SignIn, SignUp, ClerkLoading, ClerkFailed } from "@clerk/react";
import ClerkAuthProvider from "@/components/auth/ClerkAuthProvider";
import { StudioProvider } from "@/context/StudioContext";
import { AppDataProvider } from "@/context/AppDataContext";
import { Toaster } from "@/components/ui/sonner";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import Setup from "@/pages/Setup";
import Library from "@/pages/Library";
import Plans from "@/pages/Plans";
import Admin from "@/pages/Admin";

const Private = ({ children }) => (
  <>
    <Show when="signed-in">{children}</Show>
    <Show when="signed-out"><Navigate to="/sign-in" replace /></Show>
  </>
);

const AuthPage = ({ children }) => (
  <div className="min-h-[70vh] flex items-center justify-center py-16 px-4">{children}</div>
);

const Home = () => (
  <>
    <Show when="signed-in"><Navigate to="/dashboard" replace /></Show>
    <Show when="signed-out"><Landing /></Show>
    <ClerkLoading><Landing /></ClerkLoading>
    <ClerkFailed><Landing /></ClerkFailed>
  </>
);

function App() {
  return (
    <BrowserRouter>
      <ClerkAuthProvider>
        <AppDataProvider>
        <StudioProvider>
          <Header />
          <main className="min-h-[70vh]">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/sign-in/*" element={<AuthPage><SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" withSignUp /></AuthPage>} />
              <Route path="/sign-up/*" element={<AuthPage><SignUp routing="path" path="/sign-up" signInUrl="/sign-in" /></AuthPage>} />
              <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
              <Route path="/setup" element={<Private><Setup /></Private>} />
              <Route path="/library" element={<Private><Library /></Private>} />
              <Route path="/plans" element={<Private><Plans /></Private>} />
              <Route path="/admin" element={<Private><Admin /></Private>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
          <Toaster richColors position="top-right" />
        </StudioProvider>
        </AppDataProvider>
      </ClerkAuthProvider>
    </BrowserRouter>
  );
}

export default App;
