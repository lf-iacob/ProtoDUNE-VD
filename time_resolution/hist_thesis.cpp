// -- Histogram representation for thesis --

#include <TFile.h>
#include <TDirectoryFile.h>
#include <TTree.h>
#include <TH1F.h>
#include <TCanvas.h>
#include <TStyle.h>
#include <TF1.h>
#include <TPaveText.h>

// Prendo i dati dal root file
TFile *_file0 = TFile::Open("Run_39033_Ep_106_Ch_0_time_resolution.root");
TDirectoryFile* d = (TDirectoryFile*)_file0->Get("amplitude_filt_0_thr_0p5");
TTree *t = (TTree*)d->Get("time_resolution");

TH1F *hist = new TH1F("hist", "Hist t0;t0 [ticks];Entries", 84, 235, 277);

// Stile istogramma
hist->SetLineColor(kBlue); 
hist->SetLineWidth(4);
hist->SetFillColor(kBlue-4);
hist->SetFillStyle(3004);

TCanvas *c = new TCanvas("c","");
c->SetLogy();
t->Draw("t0 >> hist");

// Fit con parametri
hist->Fit("gaus", "", "", 240, 270);
hist->GetFunction("gaus")->SetLineColor(kRed);
hist->GetFunction("gaus")->SetLineWidth(3);

TF1 *f = hist->GetFunction("gaus");
double sigma = f->GetParameter(2);

c->Update();

// Box statistica+fit
  //Versione1
/*gStyle->SetOptStat(1100);
gStyle->SetStatFormat(".1f");
gStyle->SetOptFit(0011);*/
  //Versione2
gStyle->SetOptStat(0);
TPaveText *pt = new TPaveText(0.68, 0.68, 0.87, 0.87, "NDC");
pt->AddText(Form("Mean = %.1f", hist->GetMean()));
pt->AddText(Form("Std Dev  = %.1f", hist->GetRMS()));
pt->AddText(Form("Sigma (fit) = %.1f", sigma));
pt->SetFillColor(0); 
pt->SetTextColor(kBlack);
pt->SetTextFont(42);
pt->SetShadowColor(0);
pt->Draw();

c->Modified();
c->Update();


//cd /Users/lauraiacob/fisica_programming/protodune25/np02_time_resolution/raw_ana
