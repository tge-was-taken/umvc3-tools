   the_weaponData = attributes weaponData
   (
	   parameters main rollout:params
	   (
		   hitPoints type: #float ui:hits default:10
		   cost type: #float ui:cost default:100
		   sound type: #string
	   )
	   rollout params "Weapon Parameters"
	   ( 
			spinner hits "Hit Points" type: #float
			spinner cost "Cost" type: #float
			dropdownlist sound_dd "Sound" items:# ("boom","sparkle","zap","fizzle")
		)
   )