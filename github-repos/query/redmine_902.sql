SELECT `workflows`.* FROM `workflows` WHERE `workflows`.`type` IN ('WorkflowTransition') AND `workflows`.`role_id` IN (1, 2, 3, 4) AND `workflows`.`tracker_id` IN (1, 2, 3)