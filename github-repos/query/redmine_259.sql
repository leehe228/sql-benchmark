SELECT `users`.* FROM `users` WHERE `users`.`type` IN ('User', 'AnonymousUser') AND `users`.`id` IN (2, 1)