"""Shared workbench.desktop.main.js patch patterns for multiple Cursor versions."""

from branding import APP_NAME, GITHUB_URL


def get_workbench_replacements():
    """Return ordered old->new string replacements for Pro UI, limits, and server sync block."""
    return {
        # ===== Cursor 3.11+ (cs.* enums, Hgt/KAc storage keys) =====
        # --- Anti-revert membership ---
        "this.storeMembershipType=i=>{const r=this.membershipType(),s=this.subscriptionStatus();i=i??cs.FREE,this.storageService.store(Hgt": (
            "this.storeMembershipType=i=>{const r=this.membershipType(),s=this.subscriptionStatus();i=cs.PRO,this.storageService.store(Hgt"
        ),
        "default:return cs.FREE}},this.openAIKey": "default:return cs.PRO}},this.openAIKey",
        "this.storeMembershipType(cs.FREE),this._reactiveStorageService": (
            "this.storeMembershipType(cs.PRO),this._reactiveStorageService"
        ),
        "j||this.storeMembershipType(cs.FREE)": "j||this.storeMembershipType(cs.PRO)",
        "membershipType(){return this.reactiveStorageService.applicationUserPersistentStorage.membershipType}": (
            "membershipType(){return cs.PRO}"
        ),
        "this.storeSubscriptionStatus=i=>{const r=this.subscriptionStatus(),s=this.membershipType();this.storageService.store(KAc,i,-1,1)": (
            'this.storeSubscriptionStatus=i=>{const r=this.subscriptionStatus(),s=this.membershipType();i="active",this.storageService.store(KAc,i,-1,1)'
        ),
        'membershipType()===cs.FREE?"confirmed-free":"allow-full"': (
            'membershipType()===cs.ULTRA?"confirmed-free":"allow-full"'
        ),
        "this._membershipType=()=>this.storageService.get(Hgt,-1)": "this._membershipType=()=>cs.PRO",
        'this._subscriptionStatus=()=>this.storageService.get(KAc,-1)': (
            'this._subscriptionStatus=()=>"active"'
        ),
        'setApplicationUserPersistentStorage("membershipType",this.storageService.get(Hgt,-1))': (
            'setApplicationUserPersistentStorage("membershipType",cs.PRO)'
        ),
        "this.storeMembershipType(ee.membershipType),this.storeSubscriptionStatus(ee.subscriptionStatus)": (
            'this.storeMembershipType(cs.PRO),this.storeSubscriptionStatus("active")'
        ),
        'case cs.FREE:return"Free Pla': 'case cs.FREE:return"Pro Pla',
        # --- Block auth/membership server sync ---
        'this.refreshMembership=async()=>{this.authDebugLog("refreshMembership: called");const J=this.accessToken()': (
            "this.refreshMembership=async()=>{return;const J=this.accessToken()"
        ),
        "async refreshAuthentication(){await this.getAccessToken()||await this.refreshAccessToken(),await this.refreshMembership()}": (
            "async refreshAuthentication(){return}"
        ),
        "scheduleTeamPolicyCheck(){this.hasScheduledTeamPolicyCheck||(this.hasScheduledTeamPolicyCheck=!0,setTimeout(()=>{this.hasScheduledTeamPolicyCheck=!1,this.runTeamPolicyCheck()},3e3))}": (
            "scheduleTeamPolicyCheck(){return}"
        ),
        "const je=async()=>{try{await this.cursorAuthenticationService.refreshMembership(),this._authenticationRefreshBackoffAttempts=0}": (
            "const je=async()=>{return;try{await this.cursorAuthenticationService.refreshMembership(),this._authenticationRefreshBackoffAttempts=0}"
        ),
        "this.authenticationRefreshTimeoutId=Cn.setTimeout(je,Et+Rt)};je();const st=10;": (
            "this.authenticationRefreshTimeoutId=Cn.setTimeout(je,Et+Rt)};/*je();*/const st=10;"
        ),
        "setTimeout(()=>{n.cursorAuthenticationService.refreshMembership()},2e3)": (
            "setTimeout(()=>{},2e3)"
        ),
        "Br(()=>{e.cursorAuthenticationService.refreshMembership().then(": (
            "Br(()=>{Promise.resolve().then("
        ),
        # --- Block usage/pricing/privacy server sync ---
        "this.fetchUserPricingInfo=async()=>{try{const W=await": (
            "this.fetchUserPricingInfo=async()=>{return;try{const W=await"
        ),
        "this.fetchUserPrivacyMode=async J=>{const W=this.inferPrivacyModeFromLegacyValues()": (
            "this.fetchUserPrivacyMode=async J=>{return;const W=this.inferPrivacyModeFromLegacyValues()"
        ),
        'async getTeams(){this.authDebugLog("getTeams: called");const n=await this.dashboardClient()': (
            'async getTeams(){return[];const n=await this.dashboardClient()'
        ),
        "async performFetch(n){this.setIsLoading(!0),this.setError(null);try{const t=await(await this.cursorAuthenticationService.dashboardClient()).getCurrentPeriodUsage": (
            "async performFetch(n){return;this.setIsLoading(!0),this.setError(null);try{const t=await(await this.cursorAuthenticationService.dashboardClient()).getCurrentPeriodUsage"
        ),
        "async refetch(n=!1){if(!this.cursorAuthenticationService.isAuthenticated())return": (
            "async refetch(n=!1){return;if(!this.cursorAuthenticationService.isAuthenticated())return"
        ),
        "async fetchPlanInfo(n=!1){if(!this.cursorAuthenticationService.isAuthenticated())return": (
            "async fetchPlanInfo(n=!1){return;if(!this.cursorAuthenticationService.isAuthenticated())return"
        ),
        "addLoginChangedListener(J=>{J?this.fetchUserPricingInfo().catch": (
            "addLoginChangedListener(J=>{J?Promise.resolve().catch"
        ),
        "addSubscriptionChangedListener(()=>{this.fetchUserPricingInfo().catch": (
            "addSubscriptionChangedListener(()=>{Promise.resolve().catch"
        ),
        # ===== Cursor 3.10.x legacy (Vr.* enums, Zmt/k8i keys) =====
        "storeMembershipType=s=>{const o=this.membershipType(),a=this.subscriptionStatus();s=s??Vr.FREE,this.storageService.store(Zmt,s,-1,1)": (
            "storeMembershipType=s=>{const o=this.membershipType(),a=this.subscriptionStatus();s=Vr.PRO,this.storageService.store(Zmt,s,-1,1)"
        ),
        "default:return Vr.FREE}},this.openAIKey": "default:return Vr.PRO}},this.openAIKey",
        "z||this.storeMembershipType(Vr.FREE)": "z||this.storeMembershipType(Vr.PRO)",
        "this.storeMembershipType(Vr.FREE),this._reactiveStorageService": (
            "this.storeMembershipType(Vr.PRO),this._reactiveStorageService"
        ),
        "this.storeSubscriptionStatus=s=>{const o=this.subscriptionStatus(),a=this.membershipType();this.storageService.store(k8i,s,-1,1)": (
            'this.storeSubscriptionStatus=s=>{const o=this.subscriptionStatus(),a=this.membershipType();s="active",this.storageService.store(k8i,s,-1,1)'
        ),
        'membershipType()===Vr.FREE?"confirmed-free":"allow-full"': (
            'membershipType()===Vr.ULTRA?"confirmed-free":"allow-full"'
        ),
        "this._membershipType=()=>this.storageService.get(Zmt,-1)": "this._membershipType=()=>Vr.PRO",
        'this._subscriptionStatus=()=>this.storageService.get(k8i,-1)': (
            'this._subscriptionStatus=()=>"active"'
        ),
        'setApplicationUserPersistentStorage("membershipType",this.storageService.get(Zmt,-1))': (
            'setApplicationUserPersistentStorage("membershipType",Vr.PRO)'
        ),
        "this.storeMembershipType(J.membershipType),this.storeSubscriptionStatus(J.subscriptionStatus)": (
            'this.storeMembershipType(Vr.PRO),this.storeSubscriptionStatus("active")'
        ),
        'this.refreshMembership=async()=>{this.authDebugLog("refreshMembership: called");const U=this.accessToken()': (
            "this.refreshMembership=async()=>{return;const U=this.accessToken()"
        ),
        "const We=async()=>{try{await this.cursorAuthenticationService.refreshMembership(),this._authenticationRefreshBackoffAttempts=0}": (
            "const We=async()=>{return;try{await this.cursorAuthenticationService.refreshMembership(),this._authenticationRefreshBackoffAttempts=0}"
        ),
        "this.authenticationRefreshTimeoutId=Sn.setTimeout(We,Ct+Dt)};We();const Qe=10;": (
            "this.authenticationRefreshTimeoutId=Sn.setTimeout(We,Ct+Dt)};/*We();*/const Qe=10;"
        ),
        "setTimeout(()=>{e.cursorAuthenticationService.refreshMembership()},2e3)": (
            "setTimeout(()=>{},2e3)"
        ),
        "xr(()=>{t.cursorAuthenticationService.refreshMembership().then(": (
            "xr(()=>{Promise.resolve().then("
        ),
        "async performFetch(e){this.setIsLoading(!0),this.setError(null);try{const n=await(await this.cursorAuthenticationService.dashboardClient()).getUsageLimitStatusAndActiveGrants": (
            "async performFetch(e){return;this.setIsLoading(!0),this.setError(null);try{const n=await(await this.cursorAuthenticationService.dashboardClient()).getUsageLimitStatusAndActiveGrants"
        ),
        "async refetch(e=!1){if(!this.cursorAuthenticationService.isAuthenticated())return": (
            "async refetch(e=!1){return;if(!this.cursorAuthenticationService.isAuthenticated())return"
        ),
        # ===== Shared UI / limits =====
        r'B(k,D(Ln,{title:"Upgrade to Pro",size:"small",get codicon(){return A.rocket},get onClick(){return t.pay}}),null)': (
            r'B(k,D(Ln,{title:"' + APP_NAME + r'",size:"small",get codicon(){return A.github},'
            r'get onClick(){return function(){window.open("' + GITHUB_URL + r'","_blank")}}}),null)'
        ),
        r'M(x,I(as,{title:"Upgrade to Pro",size:"small",get codicon(){return $.rocket},get onClick(){return t.pay}}),null)': (
            r'M(x,I(as,{title:"' + APP_NAME + r'",size:"small",get codicon(){return $.rocket},'
            r'get onClick(){return function(){window.open("' + GITHUB_URL + r'","_blank")}}}),null)'
        ),
        r'async getEffectiveTokenLimit(e){const n=e.modelName;if(!n)return 2e5;': (
            r'async getEffectiveTokenLimit(e){return 9000000;const n=e.modelName;if(!n)return 9e5;'
        ),
        r'<div>Pro Trial': r'<div>Pro',
        r'py-1">Auto-select': r'py-1">Bypass-Version-Pin',
        r'notifications-toasts': r'notifications-toasts hidden',
        r'return()=>Le()?"Pro Trial":r()===Vr.FREE?"Free Plan":"P': (
            r'return()=>Le()?"Pro":r()===Vr.FREE?"Pro Plan":"P'
        ),
        r'case Vr.FREE_TRIAL:return"Pro Trial"': r'case Vr.FREE_TRIAL:return"Pro"',
        r't==="trialing"?"Pro Trial":"Pro Plan"': r't==="trialing"?"Pro":"Pro Plan"',
        r'case Vr.FREE:return"Free Pla': r'case Vr.FREE:return"Pro Pla',
        r'TQo=2e5': r'TQo=9e5',
        r'RJp=2e5': r'RJp=9e5',
        r'H$u=2e5': r'H$u=9e5',
        r'Em=2e5': r'Em=9e5',
    }


def count_pending_patches(content):
    pending = 0
    for old in get_workbench_replacements():
        if _skip_replacement(old, content):
            continue
        if old in content:
            pending += 1
    return pending


def _skip_replacement(old, content):
    if old == "notifications-toasts" and "notifications-toasts hidden" in content:
        return True
    return False


def apply_workbench_patches(content):
    applied = 0
    for old, new in get_workbench_replacements().items():
        if _skip_replacement(old, content):
            continue
        if old in content:
            content = content.replace(old, new)
            applied += 1
    content = content.replace("notifications-toasts hidden hidden", "notifications-toasts hidden")
    return content, applied
