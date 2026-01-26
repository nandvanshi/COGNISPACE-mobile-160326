import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle } from 'lucide-react';

const ClinicalDisclaimer = () => {
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
          <h1 className="text-4xl font-serif text-primary mb-4">Clinical Disclaimer</h1>
          <p className="text-muted-foreground">Important information about COGNISPACE</p>
        </div>

        {/* Important Notice Box */}
        <div className="bg-warning/10 border-2 border-warning/30 p-8 rounded-2xl mb-12">
          <div className="flex items-start gap-4">
            <AlertTriangle className="text-warning flex-shrink-0 mt-1" size={32} />
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-3">Important Notice</h2>
              <p className="text-foreground leading-relaxed">
                COGNISPACE is a <strong>practice management and clinical support platform</strong>. 
                It is NOT a healthcare provider and does not provide medical or psychological treatment. 
                All clinical responsibility remains with the registered, licensed therapist.
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="prose prose-slate max-w-none space-y-8">
          
          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Platform Purpose</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE is designed to assist mental health professionals in managing their practice 
              and supporting clinical documentation. The platform provides tools for:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Practice management (appointments, clients, payments)</li>
              <li>Clinical documentation (session notes, assessments)</li>
              <li>AI-assisted clinical support features</li>
              <li>Communication with clients</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">2. Not a Healthcare Provider</h2>
            <div className="bg-surface p-6 rounded-xl">
              <p className="text-foreground leading-relaxed">
                COGNISPACE and Vedic Wellness Solutions are <strong>NOT</strong>:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
                <li>A healthcare provider or medical facility</li>
                <li>A substitute for professional mental health treatment</li>
                <li>A crisis intervention or emergency service</li>
                <li>A diagnostic or treatment recommendation system</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">3. AI Features Disclaimer</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE includes AI-powered features such as:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li><strong>TheraGenie:</strong> Assessment suggestions, protocol generation, homework creation</li>
              <li><strong>CogniVision:</strong> AI-assisted diagnostic report drafting</li>
            </ul>
            
            <div className="bg-error/10 border border-error/20 p-6 rounded-xl mt-6">
              <h3 className="text-lg font-medium text-error mb-3">Critical Understanding:</h3>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2">
                <li>AI features are <strong>assistive tools only</strong>, not autonomous decision-makers</li>
                <li>All AI-generated content must be <strong>reviewed and edited</strong> by the therapist</li>
                <li>AI outputs do NOT constitute medical advice, diagnosis, or treatment</li>
                <li>The AI may produce errors, inaccuracies, or inappropriate suggestions</li>
                <li>Therapists must apply professional judgment to all AI outputs</li>
                <li>The platform does NOT independently diagnose or treat any condition</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">4. Therapist Responsibility</h2>
            <p className="text-muted-foreground leading-relaxed">
              All clinical decisions, diagnoses, treatment plans, and patient care remain the 
              <strong> sole responsibility of the licensed therapist</strong>. By using COGNISPACE, therapists acknowledge:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>They hold valid professional licensure in their jurisdiction</li>
              <li>They will not rely solely on AI features for clinical decisions</li>
              <li>They will verify and approve all AI-generated content before use</li>
              <li>They maintain full professional and legal liability for patient care</li>
              <li>They will comply with all applicable mental health laws and ethics codes</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">5. Client Understanding</h2>
            <p className="text-muted-foreground leading-relaxed">
              Clients using COGNISPACE should understand:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>The platform facilitates communication with your therapist</li>
              <li>Any reports or assessments are created by your therapist, not the platform</li>
              <li>For emergencies, contact emergency services (112) or your nearest hospital</li>
              <li>The platform is not a substitute for direct communication with your therapist</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. Emergency Situations</h2>
            <div className="bg-error/10 border-2 border-error/30 p-6 rounded-xl">
              <h3 className="text-lg font-semibold text-error mb-3">If you are in crisis:</h3>
              <p className="text-foreground leading-relaxed mb-4">
                COGNISPACE is NOT an emergency service. If you or someone you know is in immediate danger:
              </p>
              <ul className="list-disc pl-6 text-foreground space-y-2">
                <li>Call <strong>112</strong> (Emergency Services - India)</li>
                <li>Call <strong>iCall:</strong> 9152987821 (Mental Health Helpline)</li>
                <li>Call <strong>Vandrevala Foundation:</strong> 1860-2662-345</li>
                <li>Visit your nearest hospital emergency department</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">7. Limitation of Liability</h2>
            <p className="text-muted-foreground leading-relaxed">
              Vedic Wellness Solutions and COGNISPACE shall not be liable for:
            </p>
            <ul className="list-disc pl-6 text-muted-foreground space-y-2 mt-4">
              <li>Any clinical outcomes, treatment decisions, or patient care</li>
              <li>Errors, inaccuracies, or omissions in AI-generated content</li>
              <li>Misuse of platform features by users</li>
              <li>Actions taken based on AI suggestions without professional review</li>
              <li>Any direct, indirect, or consequential damages arising from platform use</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Regulatory Compliance</h2>
            <p className="text-muted-foreground leading-relaxed">
              COGNISPACE is designed to support compliance with Indian mental health regulations 
              and ethical guidelines. However, ensuring compliance remains the responsibility of 
              the individual therapist based on their jurisdiction and professional body requirements.
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

        </div>

        {/* Acknowledgment Box */}
        <div className="mt-12 bg-primary/5 border border-primary/20 p-6 rounded-xl">
          <p className="text-sm text-foreground text-center">
            By using COGNISPACE, you acknowledge that you have read, understood, and agree to this 
            Clinical Disclaimer. If you do not agree, please discontinue use of the platform.
          </p>
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>© 2026 COGNISPACE by Vedic Wellness Solutions. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default ClinicalDisclaimer;
