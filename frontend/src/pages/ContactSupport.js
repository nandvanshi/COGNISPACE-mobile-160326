import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, MapPin, Phone, Building2, FileText } from 'lucide-react';

const ContactSupport = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-surface to-white">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Back Link */}
        <Link 
          to="/login" 
          className="inline-flex items-center text-primary hover:text-primary/80 mb-8"
        >
          <ArrowLeft size={18} className="mr-2" />
          Back to Login
        </Link>

        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-serif text-primary mb-4">Contact & Support</h1>
          <p className="text-muted-foreground">We're here to help you</p>
        </div>

        {/* Contact Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          
          {/* Email Card */}
          <div className="bg-white/70 backdrop-blur-xl border border-border/40 rounded-2xl p-8">
            <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
              <Mail className="text-primary" size={28} />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Email Support</h3>
            <p className="text-muted-foreground mb-4">
              For general inquiries, technical support, and feedback
            </p>
            <a 
              href="mailto:care@cognispace.in" 
              className="text-primary hover:underline font-medium text-lg"
            >
              care@cognispace.in
            </a>
            <p className="text-sm text-muted-foreground mt-2">
              We typically respond within 24-48 hours
            </p>
          </div>

          {/* Support Tickets Card */}
          <div className="bg-white/70 backdrop-blur-xl border border-border/40 rounded-2xl p-8">
            <div className="w-14 h-14 bg-info/10 rounded-xl flex items-center justify-center mb-4">
              <FileText className="text-info" size={28} />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Support Tickets</h3>
            <p className="text-muted-foreground mb-4">
              For logged-in users, detailed issue tracking and resolution
            </p>
            <div className="bg-surface p-4 rounded-lg">
              <p className="text-sm text-foreground">
                <strong>How to raise a ticket:</strong>
              </p>
              <ol className="list-decimal list-inside text-sm text-muted-foreground mt-2 space-y-1">
                <li>Login to your COGNISPACE account</li>
                <li>Navigate to Support section</li>
                <li>Click "Create New Ticket"</li>
                <li>Describe your issue in detail</li>
              </ol>
            </div>
          </div>

        </div>

        {/* Company Information */}
        <div className="bg-white/70 backdrop-blur-xl border border-border/40 rounded-2xl p-8 mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-6 flex items-center gap-3">
            <Building2 className="text-primary" size={28} />
            Company Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-foreground mb-3">Vedic Wellness Solutions</h3>
              <div className="space-y-3 text-muted-foreground">
                <p className="flex items-start gap-3">
                  <MapPin size={18} className="text-primary flex-shrink-0 mt-1" />
                  <span>
                    SBI Colony, Plot No C-1B, Gayatripura,<br />
                    Kursi Road, Lucknow,<br />
                    Uttar Pradesh, 226022<br />
                    India
                  </span>
                </p>
                <p className="flex items-center gap-3">
                  <Mail size={18} className="text-primary" />
                  <a href="mailto:care@cognispace.in" className="hover:text-primary">
                    care@cognispace.in
                  </a>
                </p>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-foreground mb-3">Legal Information</h3>
              <div className="space-y-3 text-muted-foreground">
                <p><strong>GSTIN:</strong> 09APSPD8480L1Z2</p>
                <p><strong>Registered Name:</strong> Vedic Wellness Solutions</p>
                <p><strong>Platform:</strong> COGNISPACE</p>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-6">Frequently Asked Questions</h2>
          
          <div className="space-y-4">
            <div className="bg-surface rounded-xl p-6">
              <h3 className="font-medium text-foreground mb-2">How do I reset my password?</h3>
              <p className="text-sm text-muted-foreground">
                Contact your therapist or use the admin support if you're a therapist. 
                Email care@cognispace.in for assistance.
              </p>
            </div>
            
            <div className="bg-surface rounded-xl p-6">
              <h3 className="font-medium text-foreground mb-2">How do I register as a therapist?</h3>
              <p className="text-sm text-muted-foreground">
                Click "Register as Therapist" on the login page. Fill out the application form 
                with your credentials. Registration requires admin approval.
              </p>
            </div>
            
            <div className="bg-surface rounded-xl p-6">
              <h3 className="font-medium text-foreground mb-2">How do clients get access?</h3>
              <p className="text-sm text-muted-foreground">
                Clients are added by their therapist. Therapists can create client accounts or 
                share their unique registration link for client self-registration.
              </p>
            </div>
            
            <div className="bg-surface rounded-xl p-6">
              <h3 className="font-medium text-foreground mb-2">Is my data secure?</h3>
              <p className="text-sm text-muted-foreground">
                Yes. We use industry-standard encryption and security measures. 
                Read our <Link to="/privacy-policy" className="text-primary hover:underline">Privacy Policy</Link> for details.
              </p>
            </div>
            
            <div className="bg-surface rounded-xl p-6">
              <h3 className="font-medium text-foreground mb-2">What are the subscription plans?</h3>
              <p className="text-sm text-muted-foreground">
                Contact us at care@cognispace.in for information about subscription plans 
                and pricing for your practice.
              </p>
            </div>
          </div>
        </div>

        {/* Business Hours */}
        <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 mb-12">
          <h3 className="font-semibold text-foreground mb-3">Support Hours</h3>
          <p className="text-muted-foreground">
            Monday - Saturday: 10:00 AM - 6:00 PM IST<br />
            Sunday: Closed
          </p>
          <p className="text-sm text-muted-foreground mt-3">
            For urgent technical issues outside business hours, please email with "URGENT" in the subject line.
          </p>
        </div>

        {/* Legal Links */}
        <div className="flex flex-wrap gap-4 justify-center text-sm">
          <Link to="/privacy-policy" className="text-primary hover:underline">Privacy Policy</Link>
          <span className="text-muted-foreground">•</span>
          <Link to="/terms-conditions" className="text-primary hover:underline">Terms & Conditions</Link>
          <span className="text-muted-foreground">•</span>
          <Link to="/clinical-disclaimer" className="text-primary hover:underline">Clinical Disclaimer</Link>
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>© 2026 COGNISPACE by Vedic Wellness Solutions. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default ContactSupport;
