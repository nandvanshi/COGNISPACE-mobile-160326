import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const PrivacyPolicy = () => {
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
          <h1 className="text-4xl font-serif text-primary mb-4">Privacy Policy</h1>
          <p className="text-muted-foreground">Last updated: January 2026</p>
        </div>

        {/* Content */}
        <div className="prose prose-slate max-w-none space-y-8">
          
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Introduction</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE, a product of <strong>Vedic Wellness Solutions</strong>, is committed to protecting the privacy 
              and security of all data collected through our platform. This Privacy Policy explains how we collect, 
              use, store, and protect information from therapists, clients, and other users of our practice 
              management platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">2. Information We Collect</h2>
            
            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">2.1 Therapist Information</h3>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2">
              <li>Full name, credentials, and professional qualifications</li>
              <li>Contact information (mobile number, email address)</li>
              <li>Practice address and clinic details</li>
              <li>Bank account details for payment processing</li>
              <li>Professional registration numbers</li>
            </ul>

            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">2.2 Client Information</h3>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2">
              <li>Basic demographic information (name, age, contact details)</li>
              <li>Emergency contact information</li>
              <li>Appointment history and session notes (managed by therapist)</li>
              <li>Assessment results and clinical documentation</li>
              <li>Payment records and receipts</li>
            </ul>

            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">2.3 Technical Information</h3>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2">
              <li>Device information and browser type</li>
              <li>IP address and login timestamps</li>
              <li>Usage patterns and feature interactions</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2">
              <li>To provide and maintain the COGNISPACE platform services</li>
              <li>To facilitate appointment scheduling and reminders</li>
              <li>To send notifications via email and WhatsApp (with consent)</li>
              <li>To generate payment receipts and financial records</li>
              <li>To provide AI-assisted clinical support tools (for therapists only)</li>
              <li>To improve platform functionality and user experience</li>
              <li>To comply with legal and regulatory requirements</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">4. Data Storage & Security</h2>
            <p className="text-muted-foreground leading-relaxed">
              All data is stored on secure, encrypted servers. We implement industry-standard security measures 
              including:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>End-to-end encryption for sensitive clinical data</li>
              <li>Secure authentication with JWT tokens</li>
              <li>Regular security audits and vulnerability assessments</li>
              <li>Access controls and role-based permissions</li>
              <li>Secure backup and disaster recovery procedures</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">5. Email & WhatsApp Notifications</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE uses email (via Resend) and WhatsApp (via Twilio) for:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Appointment confirmations and reminders</li>
              <li>Session note reminders for therapists</li>
              <li>Subscription status notifications</li>
              <li>Important platform updates</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-4">
              Notification preferences can be managed in your account settings. Therapists can enable or 
              disable notifications based on their subscription plan.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. Data Sharing</h2>
            <p className="text-muted-foreground leading-relaxed">
              We do not sell, trade, or rent personal information to third parties. Data may be shared only:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Between therapist and their registered clients (within the platform)</li>
              <li>With payment processors for transaction handling</li>
              <li>When required by law or court order</li>
              <li>With service providers under strict confidentiality agreements</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">7. Your Rights</h2>
            <p className="text-muted-foreground leading-relaxed">
              Under applicable Indian data protection laws, you have the right to:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Access your personal data held by us</li>
              <li>Request correction of inaccurate information</li>
              <li>Request deletion of your account and data</li>
              <li>Withdraw consent for notifications</li>
              <li>Export your data in a portable format</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Data Retention</h2>
            <p className="text-muted-foreground leading-relaxed">
              Clinical records are retained as per Indian medical record-keeping guidelines. Upon account 
              deletion, personal data is removed within 30 days, except where retention is required by law 
              or for legitimate business purposes.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">9. Contact Information</h2>
            <div className="bg-surface p-6 rounded-xl">
              <p className="font-medium text-foreground mb-2">Vedic Wellness Solutions</p>
              <p className="text-muted-foreground text-sm">GSTIN: 09APSPD8480L1Z2</p>
              <p className="text-muted-foreground text-sm mt-2">
                SBI Colony, Plot No C-1B, Gayatripura,<br />
                Kursi Road, Lucknow, Uttar Pradesh, 226022
              </p>
              <p className="text-muted-foreground text-sm mt-2">
                Email: <a href="mailto:care@cognispace.in" className="text-primary hover:underline">care@cognispace.in</a>
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">10. Changes to This Policy</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may update this Privacy Policy periodically. Significant changes will be communicated via 
              email or platform notification. Continued use of COGNISPACE after changes constitutes 
              acceptance of the updated policy.
            </p>
          </section>

        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>© 2026 COGNISPACE by Vedic Wellness Solutions. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
