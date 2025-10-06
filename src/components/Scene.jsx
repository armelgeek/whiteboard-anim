import React from 'react';
import SceneObject from './SceneObject';

const Scene = ({ 
  content, 
  isActive, 
  backgroundImage,
  objects = [],
  selectedObjectId,
  onSelectObject,
  onUpdateObject,
  onDeleteObject,
  isEditing = false,
}) => {
  return (
    <div
      className={`scene absolute w-full h-full transition-opacity duration-1000 ${
        isActive ? 'opacity-100 z-10' : 'opacity-0 z-0'
      }`}
      style={{
        backgroundImage: backgroundImage ? `url(${backgroundImage})` : 'none',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        top: 0,
        left: 0,
      }}
      onClick={() => isEditing && onSelectObject && onSelectObject(null)}
    >
      <div className="relative h-full flex flex-col items-center justify-center p-8 bg-black bg-opacity-40">
        <div 
          className={`text-content ${
            isActive ? 'animate-in' : ''
          }`}
        >
          <div className="text-xl md:text-2xl text-white text-center max-w-3xl drop-shadow-md">
            {content}
          </div>
        </div>
      </div>

      {/* Render scene objects */}
      {objects && objects.map((obj) => (
        <SceneObject
          key={obj.id}
          object={obj}
          isSelected={selectedObjectId === obj.id}
          onSelect={onSelectObject}
          onUpdate={onUpdateObject}
          onDelete={onDeleteObject}
          isEditing={isEditing}
        />
      ))}
    </div>
  );
};

export default Scene;
