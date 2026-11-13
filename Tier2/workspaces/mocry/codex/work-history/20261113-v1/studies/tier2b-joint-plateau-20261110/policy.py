"""A frozen validation-only plateau controller; no test values enter this module."""
POLICIES=["fixed","lr_only","reg_only","combined"]
LR_LEVELS=[.003,.001,.0003,.0001]
WD_LEVELS=[.0001,.001,.003,.01]
DROPOUT_LEVELS=[.1,.2,.3,.4]
PLATEAU_EPOCHS=5
EARLY_STOP_EPOCHS=30
MAX_EPOCHS=120
MIN_DELTA=1e-5


def hyperparameters(policy,stage):
    assert policy in POLICIES and 0<=stage<=3
    return {"lr":LR_LEVELS[stage] if policy in ("lr_only","combined") else LR_LEVELS[0],
        "weight_decay":WD_LEVELS[stage] if policy in ("reg_only","combined") else WD_LEVELS[0],
        "dropout":DROPOUT_LEVELS[stage] if policy in ("reg_only","combined") else DROPOUT_LEVELS[0]}


class PlateauController:
    def __init__(self,policy):
        self.policy=policy;self.stage=0;self.stale=0;self.events=[]

    def after_epoch(self,epoch,global_step,validation_improved,best_validation):
        self.stale=0 if validation_improved else self.stale+1
        if self.policy=="fixed" or self.stage>=3 or self.stale<PLATEAU_EPOCHS:return None
        before=hyperparameters(self.policy,self.stage);oldstage=self.stage
        self.stage+=1;self.stale=0
        event={"epoch":epoch,"global_step":global_step,"from_stage":oldstage,"to_stage":self.stage,
            "no_improvement_complete_epochs":PLATEAU_EPOCHS,"best_joint_validation":best_validation,
            "before":before,"after":hyperparameters(self.policy,self.stage)}
        self.events.append(event);return event
