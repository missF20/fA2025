import React, { useState, useEffect } from 'react';
import { Card, Button, ProgressBar, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaCog, FaInfoCircle } from 'react-icons/fa';
import TokenUsageWidget from './TokenUsageWidget';

/**
 * Token Usage Card Component
 * 
 * A card container for the token usage widget to be displayed below conversations
 */
const TokenUsageCard: React.FC = () => {
  return (
    <div className="mt-4">
      <Card className="shadow-sm">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Token Usage Summary</h5>
          </div>
        </Card.Header>
        <Card.Body>
          <TokenUsageWidget />
        </Card.Body>
      </Card>
    </div>
  );
};

export default TokenUsageCard;