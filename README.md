Drop real assets in here, named by id (matching backend/app/config.py):

  drivers/{DRIVER_ID}.avif       e.g. drivers/VER.avif      (headshot, circular crop, used in avatars/sidebars)
  drivers-full/{DRIVER_ID}.avif  e.g. drivers-full/VER.avif (FULL-BODY shot, transparent bg, used on the Driver Profile page)
  teams/{team_id}.avif        e.g. teams/redbull.avif (team logo, transparent bg)
  cars/{team_id}.avif         e.g. cars/redbull.avif  (car cutout, transparent bg)
  circuits/{circuit_id}.svg   e.g. circuits/monza.svg (track outline)

The frontend's <Media> component already points at these paths and falls
back to the hand-drawn placeholder (crest / monogram / line-art) if a file
is missing, so you can drop assets in incrementally — nothing breaks in
the meantime.
