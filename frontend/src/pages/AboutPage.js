import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { 
  Shield, 
  Users, 
  Calendar, 
  FileText, 
  Heart, 
  Lock, 
  Clock, 
  IndianRupee,
  UserCheck,
  Building2,
  Stethoscope,
  ArrowLeft
} from 'lucide-react';

const AboutPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <button 
            onClick={() => navigate('/login')}
            className="flex items-center gap-2 text-slate-600 hover:text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Login</span>
          </button>
          <img src="/logo-cognispace.png" alt="COGNISPACE" className="h-10 object-contain" />
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-teal-50/30" />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif text-primary mb-4 tracking-tight">
            COGNISPACE
          </h1>
          <p className="text-xl sm:text-2xl text-slate-600 font-light mb-6">
            Precision Insights. Personal Growth.
          </p>
          <p className="text-base sm:text-lg text-slate-500 max-w-2xl mx-auto leading-relaxed">
            A secure clinical workspace designed to support therapists in delivering 
            structured, ethical, and consistent care.
          </p>
        </div>
      </section>

      {/* What is COGNISPACE */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-6 text-center">
            What is COGNISPACE?
          </h2>
          <p className="text-slate-600 text-center max-w-3xl mx-auto mb-10 leading-relaxed">
            COGNISPACE is a therapist-first clinical platform designed to help mental health 
            professionals manage clients, sessions, documentation, and practice operations — 
            all in one secure place.
          </p>
          
          <div className="grid sm:grid-cols-3 gap-6">
            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50">
              <Stethoscope className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-slate-700">Built for Therapists & Clinics</p>
                <p className="text-sm text-slate-500 mt-1">Designed with clinical workflows in mind</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50">
              <IndianRupee className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-slate-700">India-First Compliance</p>
                <p className="text-sm text-slate-500 mt-1">IST, ₹, Indian workflows</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-50">
              <Lock className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-slate-700">Privacy-Focused</p>
                <p className="text-sm text-slate-500 mt-1">Consent-driven & secure</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Who is it for */}
      <section className="py-16 px-4 bg-slate-50/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-10 text-center">
            Who is it for?
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* For Therapists */}
            <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <UserCheck className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-3">For Therapists</h3>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <FileText className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Case history & session notes
                </li>
                <li className="flex items-start gap-2">
                  <Calendar className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Scheduling & availability
                </li>
                <li className="flex items-start gap-2">
                  <IndianRupee className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Payments & receipts
                </li>
                <li className="flex items-start gap-2">
                  <Heart className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Optional clinical decision support
                </li>
              </ul>
            </Card>

            {/* For Clinics & Teams */}
            <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-teal-500/10 flex items-center justify-center mb-4">
                <Building2 className="w-6 h-6 text-teal-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-3">For Clinics & Teams</h3>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <Users className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Assistants for non-clinical tasks
                </li>
                <li className="flex items-start gap-2">
                  <FileText className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Reports & revenue visibility
                </li>
                <li className="flex items-start gap-2">
                  <Shield className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Controlled access & audit trails
                </li>
              </ul>
            </Card>

            {/* For Clients */}
            <Card className="p-6 bg-white border-slate-100 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center mb-4">
                <Heart className="w-6 h-6 text-amber-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-3">For Clients</h3>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <Calendar className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Appointment booking
                </li>
                <li className="flex items-start gap-2">
                  <Lock className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Secure communication
                </li>
                <li className="flex items-start gap-2">
                  <FileText className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Receipts & session history
                </li>
                <li className="flex items-start gap-2">
                  <Shield className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  Transparency & consent
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </section>

      {/* Our Philosophy */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-6">
            Our Philosophy
          </h2>
          <div className="space-y-4 text-slate-600">
            <p className="text-lg leading-relaxed">
              <span className="text-primary font-medium">Therapy is human-led.</span> Technology 
              is a support, not a substitute. Clinical judgment always stays with the therapist.
            </p>
            <div className="py-6 px-8 bg-amber-50 border border-amber-100 rounded-xl mt-8">
              <p className="text-amber-800 text-sm leading-relaxed">
                <strong>Important:</strong> COGNISPACE does not diagnose, treat, or replace clinical 
                judgment. All insights are meant to assist — never override — professional expertise.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Privacy, Ethics & Safety */}
      <section className="py-16 px-4 bg-slate-50/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-10 text-center">
            Privacy, Ethics & Safety
          </h2>
          
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              { icon: Lock, text: 'Data belongs to therapist & client' },
              { icon: FileText, text: 'Consent before therapy & documentation' },
              { icon: Shield, text: 'No clinical data shared via WhatsApp' },
              { icon: Users, text: 'Role-based access (Therapist / Assistant / Admin)' },
            ].map((item, index) => (
              <div key={index} className="flex items-center gap-3 p-4 bg-white rounded-lg border border-slate-100">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-5 h-5 text-primary" />
                </div>
                <p className="text-slate-700">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance & Standards */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-10 text-center">
            Compliance & Standards
          </h2>
          
          <div className="flex flex-wrap justify-center gap-4">
            {[
              { icon: Clock, label: 'India Standard Time (IST)' },
              { icon: Calendar, label: 'DD/MM/YYYY Date Format' },
              { icon: IndianRupee, label: 'Indian Rupee (₹)' },
              { icon: Lock, label: 'Secure Authentication' },
              { icon: FileText, label: 'Audit Logs & Access Control' },
            ].map((item, index) => (
              <div key={index} className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-full text-sm text-slate-600">
                <item.icon className="w-4 h-4 text-primary" />
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About the Platform */}
      <section className="py-16 px-4 bg-slate-50/50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-6">
            About the Platform
          </h2>
          <div className="space-y-3 text-slate-600">
            <p>Built specifically for Indian mental health workflows</p>
            <p>Scalable from solo therapist to multi-practitioner clinics</p>
            <p>Modular design — features can be enabled or disabled as needed</p>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-20 px-4 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-serif text-slate-800 mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-slate-500 mb-8">
            Join therapists across India using COGNISPACE for better practice management.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/therapist-application')}
              className="bg-primary hover:bg-primary/90 text-white px-8 py-6 text-base rounded-full"
              data-testid="about-register-therapist-btn"
            >
              Register as Therapist
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/contact')}
              className="px-8 py-6 text-base rounded-full border-slate-300"
              data-testid="about-contact-support-btn"
            >
              Contact Support
            </Button>
          </div>
          
          <p className="text-xs text-slate-400 mt-4">
            Therapist registration requires admin approval
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full py-6 px-4 border-t border-slate-200 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs text-slate-500 mb-4">
            <Link to="/privacy-policy" className="hover:text-primary transition-colors">
              Privacy Policy
            </Link>
            <span className="text-slate-300">•</span>
            <Link to="/terms-conditions" className="hover:text-primary transition-colors">
              Terms & Conditions
            </Link>
            <span className="text-slate-300">•</span>
            <Link to="/clinical-disclaimer" className="hover:text-primary transition-colors">
              Clinical Disclaimer
            </Link>
            <span className="text-slate-300">•</span>
            <Link to="/contact" className="hover:text-primary transition-colors">
              Contact / Support
            </Link>
          </div>
          
          <div className="text-center text-xs text-slate-400">
            <p>© 2026 COGNISPACE by Vedic Wellness Solutions</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AboutPage;
