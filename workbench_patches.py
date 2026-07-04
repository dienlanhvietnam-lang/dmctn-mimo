"""Shared workbench.desktop.main.js patch patterns for multiple Cursor versions."""


def get_workbench_replacements():
    """Return ordered old->new string replacements for VIP/Pro UI and limits."""
    return {
        # --- Cursor 3.x: stop refreshMembership() reverting to Free ---
        "storeMembershipType=s=>{const o=this.membershipType(),a=this.subscriptionStatus();s=s??Vr.FREE,this.storageService.store(Zmt,s,-1,1)": (
            "storeMembershipType=s=>{const o=this.membershipType(),a=this.subscriptionStatus();s=Vr.PRO,this.storageService.store(Zmt,s,-1,1)"
        ),
        "default:return Vr.FREE}},this.openAIKey": "default:return Vr.PRO}},this.openAIKey",
        "z||this.storeMembershipType(Vr.FREE)": "z||this.storeMembershipType(Vr.PRO)",
        "this.storeMembershipType(Vr.FREE),this._reactiveStorageService": (
            "this.storeMembershipType(Vr.PRO),this._reactiveStorageService"
        ),
        "membershipType(){return this.reactiveStorageService.applicationUserPersistentStorage.membershipType}": (
            "membershipType(){return Vr.PRO}"
        ),
        "this.storeSubscriptionStatus=s=>{const o=this.subscriptionStatus(),a=this.membershipType();this.storageService.store(k8i,s,-1,1)": (
            'this.storeSubscriptionStatus=s=>{const o=this.subscriptionStatus(),a=this.membershipType();s="active",this.storageService.store(k8i,s,-1,1)'
        ),
        'membershipType()===Vr.FREE?"confirmed-free":"allow-full"': (
            'membershipType()===Vr.ULTRA?"confirmed-free":"allow-full"'
        ),
        # Force read paths — API refresh runs ~2s after startup
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
        # --- Block periodic server sync (membership/token refresh loops) ---
        'this.refreshMembership=async()=>{this.authDebugLog("refreshMembership: called");const U=this.accessToken()': (
            "this.refreshMembership=async()=>{return;const U=this.accessToken()"
        ),
        "async refreshAuthentication(){await this.getAccessToken()||await this.refreshAccessToken(),await this.refreshMembership()}": (
            "async refreshAuthentication(){return}"
        ),
        "scheduleTeamPolicyCheck(){this.hasScheduledTeamPolicyCheck||(this.hasScheduledTeamPolicyCheck=!0,setTimeout(()=>{this.hasScheduledTeamPolicyCheck=!1,this.runTeamPolicyCheck()},3e3))}": (
            "scheduleTeamPolicyCheck(){return}"
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
        # Legacy patterns (Cursor <= 0.4x)
        r'B(k,D(Ln,{title:"Upgrade to Pro",size:"small",get codicon(){return A.rocket},get onClick(){return t.pay}}),null)': (
            r'B(k,D(Ln,{title:"Cursor Free VIP",size:"small",get codicon(){return A.github},'
            r'get onClick(){return function(){window.open("https://github.com/hovanhoa/cursor-free-vip","_blank")}}}),null)'
        ),
        r'M(x,I(as,{title:"Upgrade to Pro",size:"small",get codicon(){return $.rocket},get onClick(){return t.pay}}),null)': (
            r'M(x,I(as,{title:"Cursor Free VIP",size:"small",get codicon(){return $.rocket},'
            r'get onClick(){return function(){window.open("https://github.com/hovanhoa/cursor-free-vip","_blank")}}}),null)'
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
        # Token limit constants (Cursor 3.10.x)
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
