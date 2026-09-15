from ursina import *
from random import Random
import json, os, math, time
from .data.content import *

SAVE_DIR = os.path.join(os.path.expanduser('~'), 'VOIDRUNNER')
os.makedirs(SAVE_DIR, exist_ok=True)

class Player(Entity):
    def __init__(self, game):
        super().__init__(model='cube', color=color.azure, scale=(0.9,1.8,0.6), collider='box')
        self.game=game; self.hp=100; self.max_hp=100; self.armor=10; self.speed=7; self.jump=7; self.damage=1.0
        self.crit=.05; self.crit_damage=1.8; self.regen=0; self.stamina=100; self.on_ground=True; self.can_double=False; self.can_dash=False
        self.yaw=0; self.pitch=-10; self.vy=0; self.shoot_cd=0; self.reload_t=0; self.invuln=0; self.dash_cd=0
        self.weapons=[WeaponState(n,1,m,120) for n,_,_,m,_,_,_,_ in WEAPONS[:1]]
        self.weapons[0].ammo=WEAPONS[0][3]
        self.current=0; self.inventory=[]; self.currency=0; self.secrets=set(); self.achievements=set(); self.kills=0; self.damage_dealt=0
    @property
    def weapon_def(self): return WEAPONS[self.current]
    def stat(self,key):
        v=0
        for it in self.inventory:
            if it.kind=='stat' and it.stats[0]==key: v+=it.stats[1]
        return v
    def update_stats(self):
        self.max_hp=max(25,100+self.stat('max_hp')); self.armor=max(0,10+self.stat('armor')); self.speed=max(2,7*(1+self.stat('move_speed_pct')/100)); self.jump=max(4,7*(1+self.stat('jump_pct')/100)); self.damage=max(.1,1+self.stat('damage_pct')/100); self.crit=max(0,self.stat('crit_pct')/100+.05); self.crit_damage=max(1,1.8+self.stat('crit_damage_pct')/100); self.regen=max(0,self.stat('regen'))
        self.hp=min(self.hp,self.max_hp)
    def hurt(self, amount):
        if self.invuln>0: return
        blocked=min(self.armor,amount*.4); self.armor=max(0,self.armor-blocked*.15); dmg=max(1,amount-blocked); self.hp-=dmg; self.invuln=.25
        self.game.flash_damage()
        if self.hp<=0: self.game.player_died()
    def move(self):
        dt=application.time.dt; cam_f=Vec3(camera.forward.x,0,camera.forward.z).normalized(); cam_r=Vec3(camera.right.x,0,camera.right.z).normalized(); inp=Vec2(held_keys['d']-held_keys['a'], held_keys['w']-held_keys['s'])
        if inp.length(): inp=inp.normalized(); direction=(cam_r*inp.x+cam_f*inp.y).normalized(); self.position += direction*self.speed*dt; self.rotation_y=lerp(self.rotation_y, math.degrees(math.atan2(direction.x,direction.z)), 12*dt)
        if held_keys['shift']: self.position += self.forward*2.5*dt
        self.vy-=18*dt; self.y+=self.vy*dt
        hit=raycast(self.world_position+Vec3(0,-.9,0),Vec3(0,-1,0),distance=1.05,ignore=[self],debug=False)
        grounded=hit.hit and hit.entity.name not in ('Void',)
        if grounded and self.vy<=0: self.y=hit.world_point.y+0.91; self.vy=0; self.on_ground=True; self._double_used=False
        else: self.on_ground=False
    def jump_input(self):
        if not held_keys['space']:
            self._jump_lock=False
            return
        if self.on_ground and not getattr(self,'_jump_lock',False):
            self.vy=self.jump; self._jump_lock=True
        elif self.can_double and not self.on_ground and not getattr(self,'_double_used',False):
            self.vy=self.jump; self._double_used=True; self._jump_lock=True
    def dash(self):
        if self.can_dash and self.dash_cd<=0:
            self.position += self.forward*10; self.dash_cd=1.25
    def fire(self):
        if self.reload_t>0 or self.shoot_cd>0: return
        w=self.weapon_def; st=self.weapons[self.current]
        if st.ammo<=0: self.reload(); return
        st.ammo-=1; self.shoot_cd=1/max(.1,w[2]); origin=camera.world_position; direction=camera.forward
        if w[0]=='Shotgun':
            for _ in range(7): self._projectile(origin,(direction+Vec3(Random().uniform(-.05,.05),Random().uniform(-.05,.05),Random().uniform(-.05,.05))).normalized(),w[1]/1.6)
        else: self._projectile(origin,direction,w[1])
    def _projectile(self,origin,direction,base):
        hit=raycast(origin,direction,distance=self.weapon_def[5],ignore=[self],debug=False)
        if hit.hit and hasattr(hit.entity,'take_damage'):
            crit=Random().random()<self.crit; dmg=base*self.damage*(self.crit_damage if crit else 1)*self.weapons[self.current].level; hit.entity.take_damage(dmg,crit); self.damage_dealt+=dmg
        end=hit.world_point if hit.hit else origin+direction*30; beam=Entity(model='cube',color=color.rgba(90,220,255,180),scale=(.035,.035,max(.15,(end-origin).length)),position=origin); beam.look_at(origin+direction); destroy(beam,.04)
    def reload(self):
        if self.reload_t>0: return
        mag=self.weapon_def[3]; st=self.weapons[self.current]; need=mag-st.ammo; take=min(need,st.reserve); st.reserve-=take; st.ammo+=take; self.reload_t=self.weapon_def[4]
    def switch(self,idx):
        if 0<=idx<len(self.weapons): self.current=idx; self.game.hint('Weapon: '+self.weapon_def[0])
    def update(self):
        if not self.game.playing: return
        self.update_stats(); dt=application.time.dt; self.invuln=max(0,self.invuln-dt); self.shoot_cd=max(0,self.shoot_cd-dt); self.reload_t=max(0,self.reload_t-dt); self.dash_cd=max(0,self.dash_cd-dt)
        if self.regen: self.hp=min(self.max_hp,self.hp+self.regen*dt)
        self.move();
        if mouse.left: self.fire()
        if held_keys['r']: self.reload()
        self.jump_input()

class Enemy(Entity):
    def __init__(self,game,kind,pos,elite=False):
        data=next(x for x in ENEMIES if x[0]==kind); self.game=game; self.kind=kind; self.elite=elite; self.max_hp=data[2]*(1.75 if elite else 1); self.hp=self.max_hp; self.damage=data[3]*(1.5 if elite else 1); self.speed=data[4]*(1.35 if elite else 1); self.attack_cd=0; self.phase='idle'
        super().__init__(model='cube' if kind not in ('Void Drone','Sky Reaver') else 'sphere',color=color.magenta if elite else color.orange,scale=(1.2,1.6,1.2),position=pos,collider='box')
    def take_damage(self,dmg,crit=False):
        self.hp-=dmg; self.game.damage_number(dmg,crit,self.world_position+Vec3(0,1.6,0));
        if self.hp<=0: self.die()
    def die(self):
        self.game.player.kills+=1; self.game.player.currency+=5 if self.elite else 2; self.game.maybe_drop(self.world_position,self.elite); self.game.enemies.discard(self); destroy(self); self.game.check_achievement('FIRST BLOOD')
    def update(self):
        if not self.enabled or not self.game.playing:return
        p=self.game.player; d=p.world_position-self.world_position; dist=d.length(); self.attack_cd=max(0,self.attack_cd-application.time.dt)
        if dist<32:
            self.phase='chase'; self.look_at_2d(p,'y')
            if dist>2.4: self.position+=self.forward*self.speed*application.time.dt
            elif self.attack_cd<=0: p.hurt(self.damage); self.attack_cd=1.2

class Boss(Enemy):
    def __init__(self,game,name,hp,pos): super().__init__(game,'Iron Warden',pos,True); self.display_name=name; self.max_hp=hp; self.hp=hp; self.scale=(4,5,4); self.color=color.violet
    def update(self):
        if not self.game.playing:return
        super().update(); phase=1 if self.hp>self.max_hp*.75 else 2 if self.hp>self.max_hp*.5 else 3 if self.hp>self.max_hp*.25 else 4
        if Random().random()<.005*phase: self.game.spawn_wave(self.position,1+phase)
        if self.game.level_index==10 and phase>=3 and Random().random()<.01: self.game.lightning(self.game.player.world_position)

class Chest(Entity):
    def __init__(self,game,pos,rarity='Common'):
        super().__init__(model='cube',color={'Common':color.gray,'Rare':color.azure,'Epic':color.violet,'Legendary':color.yellow}.get(rarity,color.white),scale=(1.3,.8,1),position=pos,collider='box'); self.game=game; self.rarity=rarity; self.opened=False
    def update(self):
        if not self.opened and distance(self,self.game.player)<2 and held_keys['e']:
            self.opened=True; it=self.game.loot.roll(POSITIVE if Random().random()>.18 else NEGATIVE,self.game.level_index); self.game.player.inventory.append(it); self.game.player.update_stats(); self.game.item_popup(it); destroy(self); self.game.check_achievement('LEGENDARY' if it.rarity=='Legendary' else '')

class LevelBuilder:
    def __init__(self,game): self.game=game
    def build(self,idx):
        for e in self.game.level_entities: destroy(e)
        self.game.level_entities=[]; self.game.enemies=set(); rng=Random(idx*1337); theme=LEVELS[idx-1][1]; self.platform(Vec3(0,0,0),(18,1,18),self.theme_color(theme,0))
        for i in range(34+idx*4):
            ang=rng.uniform(0,math.tau); rad=8+i*2.1; x=math.cos(ang)*rad+rng.uniform(-5,5); z=math.sin(ang)*rad+rng.uniform(-5,5); y=1.4+(i%7)*1.5+rng.uniform(-.5,.8); size=rng.uniform(3,7)
            self.platform(Vec3(x,y,z),(size,rng.uniform(.5,1.5),size*.75),self.theme_color(theme,i))
            if i>2 and rng.random()<.22: self.enemy_spawn(Vec3(x,y+2,z),idx,rng)
            if rng.random()<.12: self.game.level_entities.append(Chest(self.game,Vec3(x,y+1,z),'Legendary' if rng.random()<.05 else 'Epic' if rng.random()<.15 else 'Rare' if rng.random()<.3 else 'Common'))
        for s in range(3):
            p=Vec3((s-1)*18,5+idx*.2,(idx%2*2-1)*14); self.game.level_entities.append(Chest(self.game,p,'Legendary')); self.game.level_entities.append(Entity(model='cube',color=color.rgba(90,255,220,100),scale=Vec3(1,2,1),position=p+Vec3(0,1,0)))
        if idx in BOSSES:
            bp=Vec3(0,8,62+idx*2); self.platform(bp,Vec3(25,2,25),self.theme_color(theme,9)); boss=Boss(self.game,*BOSSES[idx],bp+Vec3(0,3,0)); self.game.enemies.add(boss); self.game.boss=boss
        else:self.game.boss=None
        self.game.player.position=Vec3(0,2,0)
    def theme_color(self,t,i):
        return {'ruins':color.rgb(90,100,120),'forest':color.rgb(65,125,70),'lava':color.rgb(135,65,35),'ice':color.rgb(90,145,185),'temple':color.rgb(135,120,85),'factory':color.rgb(70,105,92),'city':color.rgb(80,95,155),'cave':color.rgb(65,55,100),'storm':color.rgb(75,80,120),'fortress':color.rgb(100,60,120)}[t]
    def platform(self,pos,scale,col): self.game.level_entities.append(Entity(model='cube',color=col,position=pos,scale=scale,collider='box'))
    def enemy_spawn(self,pos,idx,rng):
        kind=ENEMIES[rng.randrange(min(len(ENEMIES),3+idx))][0]; self.game.enemies.add(Enemy(self.game,kind,pos,rng.random()<.10+idx*.01))

class UI:
    def __init__(self,game):
        self.game=game; self.menu=Entity(parent=camera.ui); self.title=Text('VOIDRUNNER',origin=(0,0),y=.35,scale=2.6); self.subtitle=Text('3D ACTION PLATFORMER // ROGUELITE',origin=(0,0),y=.27,scale=.9); self.btns=[]
        for i,t in enumerate(['NEW GAME','CONTINUE','LOAD GAME','OPTIONS','CONTROLS','ACHIEVEMENTS','CREDITS','EXIT']): self.button(t,.10-i*.07,lambda t=t:self.click(t))
        self.menu.enabled=True; self.hud=Entity(parent=camera.ui,enabled=False); self.hp=Text(parent=self.hud,text='',position=(-.85,-.42),scale=1.1); self.weapon=Text(parent=self.hud,text='',position=(.63,-.42),scale=1.1); self.level=Text(parent=self.hud,text='',position=(-.15,.44),scale=1.0); self.shards=Text(parent=self.hud,text='',position=(.68,.44),scale=.9); self.cross=Text(parent=self.hud,text='+',origin=(0,0),scale=1.3); self.popup=Text(parent=self.hud,text='',origin=(0,0),y=.16,scale=1.2); self.hint=Text(parent=self.hud,text='',origin=(0,0),y=-.32,scale=.8)
    def button(self,label,y,fn):
        b=Button(text=label,parent=self.menu,scale=(.22,.05),y=y); b.on_click=fn; self.btns.append(b)
    def click(self,t):
        if t=='NEW GAME': self.game.new_game()
        elif t in ('CONTINUE','LOAD GAME'): self.game.load(0)
        elif t=='EXIT': application.quit()
        elif t=='OPTIONS': self.game.hint('OPTIONS: use Settings in pause menu / config.json')
        elif t=='CONTROLS': self.game.hint('WASD/ARROWS MOVE | SPACE JUMP | SHIFT SPRINT | LMB FIRE | RMB AIM | R RELOAD | 1-9 WEAPONS | E INTERACT | ESC PAUSE')
        elif t=='ACHIEVEMENTS': self.game.hint('Achievements: '+str(len(self.game.player.achievements))+'/'+str(len(ACHIEVEMENTS)))
        elif t=='CREDITS': self.game.hint('VOIDRUNNER — procedural Python edition')
    def update(self):
        p=self.game.player; self.hp.text=f'HP {int(p.hp)}/{int(p.max_hp)}  ARM {int(p.armor)}'; st=p.weapons[p.current]; self.weapon.text=f'{p.weapon_def[0]}  {st.ammo}/{st.reserve}'; self.level.text=f'LEVEL {self.game.level_index:02d} / 10'; self.shards.text=f'VOID SHARDS  {p.currency}'; self.menu.enabled=not self.game.playing; self.hud.enabled=self.game.playing
    def popup_item(self,text): self.popup.text=text; invoke(setattr,self.popup,'text','',delay=3)

class Game:
    def __init__(self):
        self.app=application; self.app.target_fps=60; window.title='VOIDRUNNER'; window.borderless=False; window.fullscreen=False; window.vsync=True; window.fps_counter.enabled=True
        self.playing=False; self.paused=False; self.level_index=1; self.level_entities=[]; self.enemies=set(); self.boss=None; self.loot=LootTable(77); self.start_time=time.time(); self.scene_root=Entity(); self.player=Player(self); self.builder=LevelBuilder(self); self.ui=UI(self); self.make_environment(); self.load(0,auto=True)
    def make_environment(self):
        Sky(color=color.rgb(8,12,22)); DirectionalLight(y=20,x=-30); AmbientLight(color=color.rgba(120,130,160,0.35)); self.void=Entity(model='plane',scale=500,position=(0,-35,0),texture=None,color=color.rgb(5,6,12)); camera.position=(0,6,-12); camera.fov=75
    def new_game(self):
        destroy(self.player); self.player=Player(self); self.start_time=time.time(); self.level_index=1; self.playing=True; self.builder.build(1); self.hint('Tutorial: WASD move | SPACE jump | LMB fire | R reload | E interact'); self.save(0)
    def start_level(self,idx): self.level_index=max(1,min(10,idx)); self.builder.build(self.level_index); self.playing=True; self.paused=False
    def player_died(self): self.player.hp=self.player.max_hp; self.player.position=(0,3,0); self.player.currency=max(0,self.player.currency-10); self.hint('YOU DIED — respawned at checkpoint')
    def maybe_drop(self,pos,elite=False):
        if Random().random()<(.16 if elite else .07): self.level_entities.append(Chest(self,pos,'Legendary' if elite and Random().random()<.35 else 'Common'))
    def spawn_wave(self,pos,n):
        rng=Random(int(time.time()*1000)%100000)
        for _ in range(n): self.enemies.add(Enemy(self,ENEMIES[rng.randrange(0,min(12,3+self.level_index))][0],pos+Vec3(rng.uniform(-8,8),2,rng.uniform(-8,8)),True))
    def lightning(self,pos):
        e=Entity(model='cube',color=color.yellow,scale=(.15,18,.15),position=pos+Vec3(0,9,0)); destroy(e,.15); self.player.hurt(20)
    def damage_number(self,dmg,crit,pos):
        t=Text(parent=scene,text=('CRIT ' if crit else '')+str(int(dmg)),position=pos,scale=1.1,color=color.yellow if crit else color.white); destroy(t,1)
    def flash_damage(self):
        e=Entity(parent=camera.ui,model='quad',color=color.rgba(255,0,0,70),scale=2); destroy(e,.08)
    def item_popup(self,it): self.ui.popup_item(f'{it.rarity.upper()}\n{it.name}\n{it.stats[0]} {it.stats[1]}')
    def hint(self,text): self.ui.hint.text=text; invoke(setattr,self.ui.hint,'text','',delay=4)
    def check_achievement(self,name):
        if name: self.player.achievements.add(name)
    def save(self,slot=0):
        data={'level':self.level_index,'hp':self.player.hp,'max_hp':self.player.max_hp,'armor':self.player.armor,'currency':self.player.currency,'current':self.player.current,'kills':self.player.kills,'secrets':list(self.player.secrets),'achievements':list(self.player.achievements),'weapons':[w.__dict__ for w in self.player.weapons],'inventory':[it.__dict__ for it in self.player.inventory],'time':time.time()-self.start_time}; open(os.path.join(SAVE_DIR,f'save{slot}.json'),'w').write(json.dumps(data,indent=2))
    def load(self,slot=0,auto=False):
        path=os.path.join(SAVE_DIR,f'save{slot}.json')
        if os.path.exists(path):
            try:
                d=json.load(open(path)); self.level_index=int(d.get('level',1)); self.player.currency=int(d.get('currency',0)); self.player.kills=int(d.get('kills',0)); self.player.current=int(d.get('current',0)); self.player.weapons=[WeaponState(w['name'],w.get('level',1),w.get('ammo',0),w.get('reserve',120)) for w in d.get('weapons',[])]; self.player.inventory=[ItemInstance(i['name'],i['rarity'],i['kind'],tuple(i['stats']),i['uid']) for i in d.get('inventory',[])]; self.player.achievements=set(d.get('achievements',[])); self.player.update_stats(); self.player.hp=self.player.max_hp; self.builder.build(self.level_index); self.playing=not auto; return
            except Exception: pass
        self.builder.build(1)
    def toggle_pause(self): self.playing=not self.playing; mouse.locked=self.playing
    def input(self,key):
        if key=='escape': self.toggle_pause()
        if not self.playing:return
        if key=='e': self.hint('Interact')
        if key=='f': self.player.dash()
        if key=='i': self.hint('INVENTORY: '+', '.join(i.name for i in self.player.inventory[-8:]) if self.player.inventory else 'empty')
        if key=='m': self.hint('MAP: LEVEL '+str(self.level_index)+' / 10')
        if key=='1': self.player.switch(0)
        if key in '23456789':
            idx=int(key)-1
            if idx<len(self.player.weapons): self.player.switch(idx)
        if key=='tab': self.save(0)
    def update(self):
        self.ui.update()
        if not self.playing:return
        self.player.can_double=self.level_index>=3; self.player.can_dash=self.level_index>=5; target=min(10,1+self.level_index//2)
        while len(self.player.weapons)<target:
            i=len(self.player.weapons); n=WEAPONS[i]; ws=WeaponState(n[0],1,n[3],120); ws.ammo=n[3]; self.player.weapons.append(ws); self.hint(f'UNLOCKED: {n[0]}')
        camera.rotation_y += mouse.velocity[0]*120; camera.rotation_x -= mouse.velocity[1]*90; camera.rotation_x=clamp(camera.rotation_x,-55,25); camera_pos=self.player.world_position+Vec3(0,2.0,0)-camera.forward*12; camera.position=lerp(camera.position,camera_pos,8*application.time.dt); camera.look_at(self.player.world_position+Vec3(0,1.4,0)); camera.fov=60 if mouse.right else 70
        if self.player.y<-20:self.player_died()
        if self.player.z>80 and not self.enemies:
            if self.level_index<10:self.start_level(self.level_index+1); self.check_achievement('VOID RUNNER')
            else:self.playing=False; self.ui.popup_item('THE VOID WARDEN DEFEATED\nVOID MASTER'); self.check_achievement('VOID MASTER'); self.save(0)
    def run(self): self.app.run()

def main():
    g=Game()
    def input_fn(key): g.input(key)
    globals()['input']=input_fn
    def update_fn(): g.update()
    globals()['update']=update_fn
    g.run()
