import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const TermsConditions = () => {
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
          <h1 className="text-4xl font-serif text-primary mb-4">Terms & Conditions</h1>
          <p className="text-muted-foreground">Effective Date: January 2026</p>
        </div>

        {/* Content */}
        <div className="prose prose-slate max-w-none space-y-8">
          
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              By accessing or using COGNISPACE, you agree to be bound by these Terms & Conditions. 
              COGNISPACE is a product of <strong>Vedic Wellness Solutions</strong>. If you do not agree 
              to these terms, please do not use the platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">2. Description of Service</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE is a practice management and clinical decision support platform designed for 
              mental health professionals. The platform provides:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Client management and appointment scheduling</li>
              <li>Session notes and clinical documentation tools</li>
              <li>Assessment administration and scoring</li>
              <li>AI-assisted clinical support features</li>
              <li>Payment tracking and receipt generation</li>
              <li>Communication tools (messaging, notifications)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">3. User Eligibility</h2>
            
            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">3.1 Therapists</h3>
            <p className="text-muted-foreground leading-relaxed">
              Therapist accounts are available to licensed mental health professionals in India. 
              Registration requires admin approval and verification of credentials.
            </p>

            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">3.2 Clients</h3>
            <p className="text-muted-foreground leading-relaxed">
              Client accounts are created by therapists for their patients. Clients cannot self-register 
              and must be added by a registered therapist or via a therapist's unique registration link.
            </p>

            <h3 className="text-lg font-medium text-foreground mt-6 mb-3">3.3 Assistants</h3>
            <p className="text-muted-foreground leading-relaxed">
              Assistant accounts are created by therapists to help manage their practice. Assistants 
              have limited access as defined by their therapist.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">4. Therapist Responsibilities</h2>
            <p className="text-muted-foreground leading-relaxed">
              By using COGNISPACE, therapists agree to:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Maintain valid professional licensure and credentials</li>
              <li>Take full clinical responsibility for all patient care decisions</li>
              <li>Review and verify all AI-generated suggestions before use</li>
              <li>Ensure client consent for data collection and notifications</li>
              <li>Maintain confidentiality of client information</li>
              <li>Comply with applicable mental health laws and ethical guidelines</li>
              <li>Not rely solely on AI features for clinical decision-making</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">5. AI Features & Clinical Disclaimer</h2>
            <div className="bg-warning/10 border border-warning/20 p-6 rounded-xl">
              <p className="text-foreground font-medium mb-3">Important Notice:</p>
              <p className="text-muted-foreground leading-relaxed">
                COGNISPACE's AI features (TheraGenie, CogniVision) are <strong>assistive tools only</strong>. 
                They are designed to support clinical decision-making, not replace professional judgment.
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
                <li>AI-generated content must be reviewed and edited by the therapist</li>
                <li>No AI output constitutes medical advice or diagnosis</li>
                <li>The platform does not provide treatment recommendations</li>
                <li>All clinical responsibility remains with the licensed therapist</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. Subscription & Payment</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE offers various subscription plans for therapists:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Subscription fees are non-refundable unless otherwise stated</li>
              <li>Features vary by subscription tier</li>
              <li>Expired subscriptions result in read-only access</li>
              <li>Trial periods may be offered at our discretion</li>
              <li>Prices are subject to change with prior notice</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">7. Prohibited Activities</h2>
            <p className="text-muted-foreground leading-relaxed">
              Users must not:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Share login credentials with unauthorized persons</li>
              <li>Use the platform for illegal activities</li>
              <li>Attempt to access other users' data without authorization</li>
              <li>Misrepresent professional credentials</li>
              <li>Use AI features to generate false clinical documentation</li>
              <li>Reverse engineer or copy platform features</li>
              <li>Violate patient confidentiality or privacy laws</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Account Termination</h2>
            <p className="text-muted-foreground leading-relaxed">
              We reserve the right to suspend or terminate accounts for:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Violation of these Terms & Conditions</li>
              <li>Fraudulent or illegal activity</li>
              <li>Non-payment of subscription fees</li>
              <li>Misuse of platform features</li>
              <li>At our sole discretion with reasonable notice</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">9. Limitation of Liability</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE and Vedic Wellness Solutions shall not be liable for:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Clinical outcomes or treatment decisions</li>
              <li>Accuracy of AI-generated suggestions</li>
              <li>Data loss due to user error or third-party actions</li>
              <li>Service interruptions beyond our reasonable control</li>
              <li>Indirect, incidental, or consequential damages</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">10. Intellectual Property</h2>
            <p className="text-muted-foreground leading-relaxed">
              All platform content, features, and functionality are owned by Vedic Wellness Solutions. 
              Users retain ownership of their clinical data but grant us a license to store and process 
              it for service delivery.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">11. Governing Law</h2>
            <p className="text-muted-foreground leading-relaxed">
              These Terms & Conditions are governed by the laws of India. Any disputes shall be subject 
              to the exclusive jurisdiction of courts in Lucknow, Uttar Pradesh.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">12. Contact Information</h2>
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
            <h2 className="text-2xl font-semibold text-foreground mb-4">13. Changes to Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may modify these terms at any time. Material changes will be communicated via email 
              or platform notification at least 30 days in advance. Continued use after changes 
              constitutes acceptance.
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

export default TermsConditions;
